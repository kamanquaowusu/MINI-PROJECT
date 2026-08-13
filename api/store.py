"""
store.py

Append-only JSONL shadow store under data/shadow/ -- matches the repo's
existing convention (data/raw/*.jsonl), needs no new dependency, and loads
with one pandas.read_json(path, lines=True) call for the future real-world
evaluation set the project PDF Section 10 calls for.

find_check() reads the file back rather than relying on an in-memory cache,
so feedback submitted after a server restart still resolves correctly.
"""

import json
import os
from pathlib import Path
from typing import Dict, Optional

from api import config

CHECKS_FILE = "checks.jsonl"
FEEDBACK_FILE = "feedback.jsonl"


def _shadow_dir() -> Path:
    d = Path(config.SHADOW_DIR)
    d.mkdir(parents=True, exist_ok=True)
    return d


def _append(filename: str, record: Dict) -> None:
    path = _shadow_dir() / filename
    line = json.dumps(record, ensure_ascii=False) + "\n"
    # O_APPEND write of a small line is atomic on POSIX.
    fd = os.open(str(path), os.O_APPEND | os.O_CREAT | os.O_WRONLY, 0o644)
    try:
        os.write(fd, line.encode("utf-8"))
    finally:
        os.close(fd)


def append_check(record: Dict) -> None:
    _append(CHECKS_FILE, record)


def append_feedback(record: Dict) -> None:
    _append(FEEDBACK_FILE, record)


def _read_all(filename: str):
    path = _shadow_dir() / filename
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


def find_check(check_id: str) -> Optional[Dict]:
    found = None
    for rec in _read_all(CHECKS_FILE):
        if rec.get("check_id") == check_id:
            found = rec  # last-match-wins, though check_ids are unique per request
    return found


def summary() -> Dict:
    checks = list(_read_all(CHECKS_FILE))
    feedback = list(_read_all(FEEDBACK_FILE))

    by_band = {"safe": 0, "suspicious": 0}
    consented = 0
    for c in checks:
        band = c.get("displayed_band")
        if band in by_band:
            by_band[band] += 1
        if c.get("consent"):
            consented += 1

    tp = fp = tn = fn = 0
    for fb in feedback:
        implied = fb.get("model_implied_label")
        user_label = fb.get("user_label")
        if implied is None or user_label is None:
            continue
        if implied == "scam" and user_label == "scam":
            tp += 1
        elif implied == "legitimate" and user_label == "scam":
            fn += 1
        elif implied == "scam" and user_label == "legitimate":
            fp += 1
        elif implied == "legitimate" and user_label == "legitimate":
            tn += 1

    confusion = None
    precision = None
    recall = None
    if (tp + fp + tn + fn) > 0:
        confusion = {"tp": tp, "fp": fp, "tn": tn, "fn": fn}
        precision = (tp / (tp + fp)) if (tp + fp) > 0 else None
        recall = (tp / (tp + fn)) if (tp + fn) > 0 else None

    return {
        "checks_total": len(checks),
        "by_band": by_band,
        "consented": consented,
        "feedback_total": len(feedback),
        "confusion": confusion,
        "precision": precision,
        "recall": recall,
        "note": "Pilot shadow data from user feedback. Not a validated benchmark.",
    }
