"""
normalize.py

Defensive text normalization for the MoMo smishing detector.

Attackers evade keyword/ML detectors two ways:
  1. Confusable characters -- swapping a Latin letter for a visually
     identical letter from another script (Cyrillic 'е' instead of Latin 'e').
  2. Invisible characters -- inserting zero-width joiners/non-joiners or a
     BOM in the middle of a word so it no longer matches known tokens.

normalize_message() undoes both, so the model always sees the clean text an
obfuscated message was trying to imitate. Validated against
data/raw/obfuscation_validation_set.jsonl (run this file directly to check).
"""

import unicodedata

# Curated table of the Cyrillic/Greek letters most commonly used to spoof
# Latin look-alikes in phishing text. Not an exhaustive Unicode confusables
# database -- covers the high-confidence, visually-identical cases.
_CONFUSABLES = {
    # Cyrillic -> Latin
    "а": "a", "А": "A",
    "е": "e", "Е": "E",
    "о": "o", "О": "O",
    "р": "p", "Р": "P",
    "с": "c", "С": "C",
    "х": "x", "Х": "X",
    "у": "y", "У": "Y",
    "і": "i", "І": "I",
    "ѕ": "s", "Ѕ": "S",
    "ј": "j", "Ј": "J",
    "к": "k", "К": "K",
    "м": "m", "М": "M",
    "н": "H",
    "т": "T",
    "в": "B",
    # Greek -> Latin
    "ο": "o", "Ο": "O",
    "α": "a", "Α": "A",
    "ι": "i", "Ι": "I",
    "κ": "k", "Κ": "K",
    "ν": "v", "Ν": "N",
    "ρ": "p", "Ρ": "P",
    "τ": "t", "Τ": "T",
    "υ": "y", "Υ": "Y",
    "χ": "x", "Χ": "X",
    "ϳ": "j",
}


def _strip_invisible(text):
    """Remove zero-width / format characters (Unicode category 'Cf')."""
    out_chars = []
    found = False
    for ch in text:
        if unicodedata.category(ch) == "Cf":
            found = True
            continue
        out_chars.append(ch)
    return "".join(out_chars), found


def _fold_confusables(text):
    """Replace known Cyrillic/Greek look-alike letters with Latin equivalents."""
    out_chars = []
    found = False
    for ch in text:
        repl = _CONFUSABLES.get(ch)
        if repl is not None:
            found = True
            out_chars.append(repl)
        else:
            out_chars.append(ch)
    return "".join(out_chars), found


def normalize_message(raw_text):
    """
    Normalize a raw SMS for the triage model.

    Returns:
        {
          "normalized_text": str,
          "had_confusable": bool,
          "had_invisible_char": bool,
          "obfuscation_suspected": bool,
        }
    """
    text = raw_text or ""

    text, had_invisible = _strip_invisible(text)
    text, had_confusable = _fold_confusables(text)
    text = unicodedata.normalize("NFKC", text)

    return {
        "normalized_text": text,
        "had_confusable": had_confusable,
        "had_invisible_char": had_invisible,
        "obfuscation_suspected": had_confusable or had_invisible,
    }


if __name__ == "__main__":
    import json

    path = "data/raw/obfuscation_validation_set.jsonl"
    total = 0
    exact_match = 0
    flag_correct = 0

    with open(path, encoding="utf-8") as f:
        for line in f:
            line = line.strip()
            if not line:
                continue
            row = json.loads(line)
            result = normalize_message(row["raw_text"])
            total += 1

            if result["normalized_text"] == row["normalized_text"]:
                exact_match += 1
            else:
                print(f"[TEXT MISMATCH {row['id']}]")
                print(f"  got:      {result['normalized_text']!r}")
                print(f"  expected: {row['normalized_text']!r}")

            if result["obfuscation_suspected"] == row["expected_flag"]:
                flag_correct += 1
            else:
                print(f"[FLAG MISMATCH {row['id']}] "
                      f"got={result['obfuscation_suspected']} expected={row['expected_flag']}")

    print(f"\nnormalized_text exact match: {exact_match}/{total}")
    print(f"obfuscation flag correct:    {flag_correct}/{total}")
