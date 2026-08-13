"""
redact.py

Best-effort PII redaction for anything persisted to the shadow log. Adapts
(copies, doesn't import -- importing dedup_and_split.py would execute its
module-level pipeline against real CSVs) the regexes already proven in
src/dedup_and_split.py's make_skeleton(), retargeted to the placeholder
tokens documented in the project PDF Section 3.2: <PHONE>, <NAME>, <AMOUNT>,
<ACCOUNT>, <REF>, <URL>.

Known limitation (documented, not a bug to fix): full-name redaction via
regex is inherently unreliable -- this only catches the dominant MoMo-alert
shape ("from KWAME", "to AMA OWUSU"). No NER; that's out of proportion for
this project and matches the PDF's own standard of best-effort placeholder
redaction, not guaranteed anonymisation.
"""

import hashlib
import re
from typing import Dict, Tuple

MAX_STORED_CHARS = 1000

RE_EXISTING_TAG = re.compile(r"<[A-Za-z_]+>")
# Broadened past http(s)/www to also catch bare domains scam SMS commonly use
# without a scheme, e.g. "momo-verify.gh", "bit.ly/x" (verified against all
# 909 real legitimate test-set messages with zero false positives).
RE_URL = re.compile(
    r"(https?://\S+|www\.\S+|\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:gh|com|co|net|org|ly|id|gy)\b(?:/\S*)?)",
    re.IGNORECASE,
)
RE_AMOUNT = re.compile(r"GH[S₵C¢]?\s?\d[\d,]*(\.\d+)?", re.IGNORECASE)
RE_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RE_TIME = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\s?(AM|PM|am|pm)?\b")
RE_PHONE = re.compile(r"\b0\d{9}\b|\+233\s?\d{9}\b")
# Hyphen-separated reference codes ("TXN-9921-04") aren't a single 5+ digit
# run, so a dedicated pattern catches them before the plain long-digit one.
RE_REF_CODE = re.compile(r"\b[A-Za-z]{2,6}-\d{2,6}(?:-\d{1,6})*\b")
RE_LONG_DIGITS = re.compile(r"\b\d{5,}\b")
# "from KWAME", "to AMA OWUSU" -- the dominant MoMo-alert name shape.
RE_NAME_AFTER_PREP = re.compile(r"(?<=\bfrom\s)([A-Z][A-Z'\- ]{2,30})|(?<=\bto\s)([A-Z][A-Z'\- ]{2,30})")


def redact(text: str) -> Tuple[str, Dict[str, int]]:
    """Return (redacted_text, counts) where counts tallies substitutions per category."""
    s = str(text)
    counts = {"url": 0, "amount": 0, "phone": 0, "ref": 0, "name": 0}

    s = RE_EXISTING_TAG.sub("<X>", s)  # normalise any tags the user pasted in

    s, n = RE_URL.subn("<URL>", s)
    counts["url"] += n

    s, n = RE_AMOUNT.subn("<AMOUNT>", s)
    counts["amount"] += n

    s, n = RE_DATE.subn("<REF>", s)
    counts["ref"] += n
    s, n = RE_TIME.subn("<REF>", s)
    counts["ref"] += n

    s, n = RE_PHONE.subn("<PHONE>", s)
    counts["phone"] += n

    s, n = RE_REF_CODE.subn("<REF>", s)
    counts["ref"] += n
    s, n = RE_LONG_DIGITS.subn("<REF>", s)
    counts["ref"] += n

    s, n = RE_NAME_AFTER_PREP.subn("<NAME>", s)
    counts["name"] += n

    s = re.sub(r"\s+", " ", s).strip()
    s = s[:MAX_STORED_CHARS]

    return s, counts


def sha256_hex(text: str) -> str:
    return hashlib.sha256(text.encode("utf-8")).hexdigest()
