"""
shadow_to_training.py

Closes the collect -> label -> retrain loop: exports LABELED, CONSENTED
messages from the app's shadow logs (data/shadow/) into a training-data
file (data/raw/shadow_labeled.jsonl) that unify.py folds into the corpus
on the next retrain.

Only two kinds of shadow records can produce a training row, because only
they carry a human-provided label -- a model prediction is never used as
its own training label (that would just reinforce the model's mistakes):

  1. Scam reports (reports.jsonl): the user explicitly reported the
     message as a scam -> label "illegitimate". The stored text is
     already redacted by api/redact.py before it ever hits disk.

  2. Labeled feedback (feedback.jsonl joined to checks.jsonl on
     check_id): feedback rows where the API derived a user_label
     ("scam" / "legitimate"). The joined check must have consent=True
     and a redacted_text -- without consent no text was stored, so
     there is nothing to train on. This is the same consent gate the
     PDF Section 8.4 requires; this script never widens it.

Safety rails:
  - Idempotent: the output file is regenerated from the shadow logs on
    every run (never appended), so re-running can't duplicate rows.
  - Conflicting labels for the same text (one user says scam, another
    says legitimate) exclude that text entirely and print a warning --
    ambiguous rows would only add noise.
  - Exact-duplicate texts collapse to one row (dedup_and_split.py's
    skeleton grouping handles near-duplicates downstream).

Run:  python src/shadow_to_training.py
Then: python src/unify.py && python src/dedup_and_split.py && python src/triage_model.py
"""

import json
from pathlib import Path

SHADOW_DIR = Path("data/shadow")
OUTPUT_PATH = Path("data/raw/shadow_labeled.jsonl")


def _read_jsonl(path):
    if not path.exists():
        return
    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            try:
                yield json.loads(line)
            except json.JSONDecodeError:
                continue


def collect_rows():
    """Return (rows, n_conflicts): labeled training rows from the shadow logs."""
    checks_by_id = {c["check_id"]: c for c in _read_jsonl(SHADOW_DIR / "checks.jsonl") if c.get("check_id")}

    # text -> {"labels": set of labels seen, "row": first exportable row}
    candidates = {}

    def add_candidate(text, label, row):
        entry = candidates.setdefault(text, {"labels": set(), "row": row})
        entry["labels"].add(label)

    # 1. Explicit scam reports -- text is stored redacted, label is the
    #    user's own assertion.
    for rpt in _read_jsonl(SHADOW_DIR / "reports.jsonl"):
        text = (rpt.get("message_redacted") or "").strip()
        if not text:
            continue
        add_candidate(text, "illegitimate", {
            "id": "shadow_{}".format(rpt.get("report_id", "rpt_unknown")),
            "text": text,
            "label": "illegitimate",
            "category": "unknown",
            "source": "report",
            "ts": rpt.get("ts"),
        })

    # 2. Feedback with a derived user label, joined to a CONSENTED check.
    for fb in _read_jsonl(SHADOW_DIR / "feedback.jsonl"):
        user_label = fb.get("user_label")
        if user_label not in ("scam", "legitimate"):
            continue
        check = checks_by_id.get(fb.get("check_id"))
        if not check or not check.get("consent") or not check.get("redacted_text"):
            continue
        text = check["redacted_text"].strip()
        if not text:
            continue
        label = "illegitimate" if user_label == "scam" else "legitimate"
        add_candidate(text, label, {
            "id": "shadow_{}".format(fb.get("feedback_id", "fb_unknown")),
            "text": text,
            "label": label,
            "category": check.get("category_input", "unknown") or "unknown",
            "source": "feedback",
            "ts": fb.get("ts"),
        })

    rows = []
    n_conflicts = 0
    for text, entry in candidates.items():
        if len(entry["labels"]) > 1:
            n_conflicts += 1
            print("  CONFLICT (excluded): users disagreed on label for: {!r}".format(text[:70]))
            continue
        row = dict(entry["row"])
        row["label"] = next(iter(entry["labels"]))
        rows.append(row)
    return rows, n_conflicts


def main():
    rows, n_conflicts = collect_rows()

    OUTPUT_PATH.parent.mkdir(parents=True, exist_ok=True)
    with open(OUTPUT_PATH, "w", encoding="utf-8") as f:
        for row in rows:
            f.write(json.dumps(row, ensure_ascii=False) + "\n")

    n_scam = sum(1 for r in rows if r["label"] == "illegitimate")
    n_legit = len(rows) - n_scam
    print("Exported {} labeled rows ({} scam, {} legitimate, {} conflicts excluded)".format(
        len(rows), n_scam, n_legit, n_conflicts))
    print("Wrote {} (regenerated in full -- safe to re-run any time)".format(OUTPUT_PATH))
    if rows:
        print("Next: python src/unify.py && python src/dedup_and_split.py && python src/triage_model.py")


if __name__ == "__main__":
    main()
