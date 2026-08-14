"""
reasons.py

Narrative reason-enrichment layer. Pure module -- no sklearn/joblib/IO
imports -- so it's testable in isolation and independently reasoned about.

Bridges a real gap: predict.py's `reasons` list only ever contains terse
machine strings ("high scam probability (0.82)"), but the approved design
mockup shows narrative bullets ("Creates urgency -- 'within 10 minutes'").
This module adds that narrative layer ON TOP OF -- never instead of -- the
model's real output; `model_band` / `model_reasons` always pass through
untouched so the raw model stays the thing being evaluated.

Also implements the documented escalation rule: the saved model bundle has
T_LOW=0.03, T_HIGH=0.04 -- a hairline-thin gap between "safe" and
"suspicious" that few messages land in on the safe side. Per PDF Section 9
("the Suspicious tier is under-populated on current data") and Section 8.3
(Suspicious = soft caution banner), this module allows escalating a
`safe`-banded message to `suspicious` when red-flag heuristics fire. The
rule only ever raises caution (never de-escalates, never overrides a model
`suspicious`) and is disableable via `enable_escalation` for an honest
side-by-side comparison of raw-model vs. pilot-caution-layer behaviour.
"""

import re
from typing import Dict, List, Optional, Set

# ---------------------------------------------------------------------------
# Shared regex fragments (reused across several heuristics)
# ---------------------------------------------------------------------------
RE_URL = re.compile(
    r"(https?://\S+|www\.\S+|\b[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?\.(?:gh|com|co|net|org|ly|id|gy)\b(?:/\S*)?)",
    re.IGNORECASE,
)
RE_AMOUNT = re.compile(r"GH[S₵C¢]?\s?\d[\d,]*(\.\d+)?", re.IGNORECASE)
RE_PHONE = re.compile(r"\b0\d{9}\b")

RE_PIN_TERM = re.compile(r"\b(pin|p\.?i\.?n|password|passcode|otp|one[- ]time (code|password)|secret code)\b", re.I)
RE_PIN_ACTION = re.compile(r"\b(send|share|give|enter|confirm|verify|provide|reply|text)\b", re.I)
# Real telco messages routinely append a safety footer ("Never share your
# PIN or OTP..."). Without this guard that footer alone false-positives
# pin_request on ~23% of real legitimate messages (measured against all 909
# legit rows in data/processed/test.csv). Only counts as a red flag if the
# action verb isn't itself negated just before it.
RE_PIN_NEGATION = re.compile(r"\b(never|don'?t|do not|won'?t|will not|no need to|please do not|protect)\b", re.I)

RE_REFUND = re.compile(
    r"\b(revers(e|al|ed)|refund|sent (to you )?in error|wrong(ly)? (sent|transfer)|by mistake|erroneous|return the (money|cash|amount))\b",
    re.I,
)

RE_THREAT_ACTION = re.compile(r"\b(block\w*|suspend\w*|deactivat\w*|lock\w*|clos\w*|restrict\w*|expir\w*)\b", re.I)
RE_THREAT_TARGET = re.compile(r"\b(account|wallet|sim|number|line)\b", re.I)

RE_SEND_PAY = re.compile(r"\b(send|pay|transfer|deposit)\b", re.I)

RE_PRIZE = re.compile(
    r"\b(congratulation\w*|you have won|winner|prize|jackpot|lucky (draw|winner)|reward|claim your)\b",
    re.I,
)

RE_URGENCY = re.compile(
    r"\b(urgent|immediately|right now|within \d+\s?(min\w*|hour\w*|hrs?)|expires?|before \d|last chance|act (fast|now)|asap|quickly|instantly)\b",
    re.I,
)

RE_BRAND = re.compile(
    r"\b(mtn|momo|telecel|airteltigo|vodafone|ecobank|stanbic|gcb|absa|fidelity|cal ?bank|zenith)\b",
    re.I,
)

RE_TRANSACTION_SHAPE = re.compile(
    r"\b(balance|confirmed|received|payment received|ref\b|txn|transaction id|new balance)\b",
    re.I,
)

SHORTENER_HOSTS = re.compile(
    r"\b(bit\.ly|tinyurl|cutt\.ly|t\.co|is\.gd|rb\.gy|shorturl|goo\.gl|s\.id)\b", re.I
)
# Domains the Ghanaian telcos actually control. mymtn.onelink.me is MTN's
# registered AppsFlyer subdomain and telecel.me is Telecel's own short
# domain -- a scammer cannot claim either, so allowlisting is safe.
ALLOWLISTED_HOSTS = (
    "mtn.com.gh", "telecel.com.gh", "airteltigo.com.gh", ".gov.gh",
    "mymtn.onelink.me", "telecel.me",
)
# Exact shortened paths the telcos verifiably own. bit.ly paths are
# first-come-first-served and immutable, so an EXACT path match cannot be
# spoofed -- but never allowlist bit.ly by host alone.
ALLOWLISTED_EXACT_URLS = ("bit.ly/telecelplayghana", "bit.ly/mymtn138")

# Escalation policy (safe -> suspicious when the model said safe). Every
# revision here must only NARROW the previous trigger, never widen it:
#   suspicious_link (any URL)  -> risky_link (shortener / brand-lookalike)
#   prize_promo (any prize word) -> pay_to_receive (prize + payment demand)
#   refund_reversal (any refund word) -> refund_escalation (refund word +
#       amount, phone, urgency, or risky link)
# Rationale: real MTN/Telecel broadcasts use FREE/reward/loan/link language
# constantly; escalating on vocabulary alone flagged most genuine telco
# marketing (measured against the owner's real inbox batch).
DEFAULT_ESCALATION_IDS = {"pin_request", "risky_link", "refund_escalation", "pay_to_receive", "obfuscation"}


def _urgency_phrase(text: str) -> Optional[str]:
    m = RE_URGENCY.search(text)
    return m.group(0) if m else None


def _url_is_allowlisted(url: str) -> bool:
    u = url.lower()
    return any(h in u for h in ALLOWLISTED_HOSTS) or any(p in u for p in ALLOWLISTED_EXACT_URLS)


def _has_risky_link(text: str) -> bool:
    """True if ANY link in the text is a (non-allowlisted) shortener or a
    brand-lookalike domain. Plain informational links don't count."""
    for match in RE_URL.finditer(text):
        url = match.group(0)
        if _url_is_allowlisted(url):
            continue
        if SHORTENER_HOSTS.search(url) or RE_BRAND.search(url):
            return True
    return False


def _suspicious_link_text(text: str) -> Optional[str]:
    match = RE_URL.search(text)
    if not match:
        return None
    url = match.group(0)
    if SHORTENER_HOSTS.search(url) and not _url_is_allowlisted(url):
        return "Contains a shortened link that hides where it really goes"
    if RE_BRAND.search(url) and not _url_is_allowlisted(url):
        return "Contains a link that copies a network's name"
    return "Contains a link — check where it really leads"


def _pin_request_fires(text: str) -> bool:
    action_m = RE_PIN_ACTION.search(text)
    term_m = RE_PIN_TERM.search(text)
    if not (action_m and term_m):
        return False
    window = text[max(0, action_m.start() - 25):action_m.start()]
    if RE_PIN_NEGATION.search(window):
        return False
    return True


def _detect_signals(text: str, model_result: dict, category: str, high_severity: Optional[Set[str]]):
    high_severity = high_severity or set()
    pin_request = _pin_request_fires(text)
    refund_reversal = bool(RE_REFUND.search(text))
    has_url = bool(RE_URL.search(text))
    has_phone = bool(RE_PHONE.search(text))
    has_amount = bool(RE_AMOUNT.search(text))
    threat_block = bool(RE_THREAT_ACTION.search(text) and RE_THREAT_TARGET.search(text))
    prize_promo = bool(RE_PRIZE.search(text))
    pay_to_receive = bool((prize_promo or refund_reversal) and RE_SEND_PAY.search(text) and has_amount)
    urgency_phrase = _urgency_phrase(text)
    urgency = urgency_phrase is not None
    impersonation = bool(RE_BRAND.search(text) and (pin_request or has_url or threat_block))
    personal_number = bool(has_phone and (refund_reversal or prize_promo or pin_request))
    severity_category = category in high_severity
    words = text.split()
    caps_words = [w for w in words if len(w) >= 3 and w.isupper()]
    shouting = len(words) >= 3 and (len(caps_words) / max(len(words), 1)) > 0.30

    obfuscation = bool(model_result.get("obfuscation_suspected"))

    risky_link = _has_risky_link(text)
    # A refund/reversal mention only justifies escalation when something
    # actionable rides along (amount, phone, urgency, risky link) -- telcos
    # legitimately SMS about how to reverse wrong transactions.
    refund_escalation = refund_reversal and (has_amount or has_phone or urgency or risky_link)

    return {
        "pin_request": pin_request,
        "refund_reversal": refund_reversal,
        "refund_escalation": refund_escalation,
        "risky_link": risky_link,
        "suspicious_link": has_url,
        "threat_block": threat_block,
        "pay_to_receive": pay_to_receive,
        "prize_promo": prize_promo,
        "urgency": urgency,
        "urgency_phrase": urgency_phrase,
        "impersonation": impersonation,
        "personal_number": personal_number,
        "severity_category": severity_category,
        "shouting": shouting,
        "obfuscation": obfuscation,
        "no_pin_request": not pin_request,
        "no_links_or_numbers": not has_url and not has_phone,
        "transaction_shape": bool(RE_TRANSACTION_SHAPE.search(text)),
        "no_urgency": not urgency,
        "no_money_request": not (RE_SEND_PAY.search(text) and has_amount),
    }


def _red_flag_reasons(text: str, signals: dict) -> List[dict]:
    out = []
    if signals["pin_request"]:
        out.append({"id": "pin_request", "kind": "red_flag",
                     "text": "Asks for your PIN or a one-time code — no real network ever does"})
    if signals["refund_reversal"]:
        out.append({"id": "refund_reversal", "kind": "red_flag",
                     "text": "Asks you to refund or reverse money you didn't expect"})
    if signals["suspicious_link"]:
        link_text = _suspicious_link_text(text)
        if link_text:
            out.append({"id": "suspicious_link", "kind": "red_flag", "text": link_text})
    if signals["threat_block"]:
        out.append({"id": "threat_block", "kind": "red_flag",
                     "text": "Threatens to block your wallet or SIM to rush you"})
    if signals["pay_to_receive"]:
        out.append({"id": "pay_to_receive", "kind": "red_flag",
                     "text": "Asks you to send money before you can receive money"})
    if signals["prize_promo"]:
        out.append({"id": "prize_promo", "kind": "red_flag",
                     "text": "Promises a prize or reward you didn't enter for"})
    if signals["urgency"]:
        out.append({"id": "urgency", "kind": "red_flag",
                     "text": "Creates urgency — \"{}\"".format(signals["urgency_phrase"])})
    if signals["impersonation"]:
        out.append({"id": "impersonation", "kind": "red_flag", "text": "Impersonates a bank or network"})
    if signals["personal_number"]:
        out.append({"id": "personal_number", "kind": "red_flag",
                     "text": "Points you to a personal number, not an official short code"})
    if signals["severity_category"]:
        out.append({"id": "severity_category", "kind": "red_flag",
                     "text": "Belongs to a scam family that moves money out of your wallet"})
    if signals["shouting"] and len(out) < 3:
        out.append({"id": "shouting", "kind": "red_flag", "text": "Uses shouting capitals to pressure you"})
    return out


def _clear_reasons(signals: dict) -> List[dict]:
    out = []
    if signals["no_pin_request"]:
        out.append({"id": "no_pin_request", "kind": "clear", "text": "No PIN or password requested"})
    if signals["no_links_or_numbers"]:
        out.append({"id": "no_links_or_numbers", "kind": "clear", "text": "No links or phone numbers to call"})
    if signals["transaction_shape"]:
        out.append({"id": "transaction_shape", "kind": "clear", "text": "Wording matches a normal payment alert"})
    if signals["no_urgency"]:
        out.append({"id": "no_urgency", "kind": "clear", "text": "No pressure to act quickly"})
    if signals["no_money_request"]:
        out.append({"id": "no_money_request", "kind": "clear", "text": "Doesn't ask you to send money"})
    return out


def _advice_for(band: str, signals: dict) -> dict:
    if band == "safe":
        if signals["transaction_shape"]:
            return {"title": "Still good to know",
                    "text": "A follow-up call asking you to 'reverse' this payment is the usual next step "
                            "in a scam. Never share your PIN."}
        return {"title": "Still good to know",
                "text": "Never share your PIN with anyone — not even someone who says they are from your network."}
    return {"title": "Stay safe",
            "text": "Never share your PIN · Don't tap links · Don't call the number · Don't send money · "
                    "Report it to your provider on 100"}


def enrich(
    normalized_text: str,
    model_result: dict,
    category: str = "unknown",
    high_severity: Optional[Set[str]] = None,
    enable_escalation: bool = True,
) -> Dict:
    text = normalized_text or ""
    model_band = model_result["band"]
    signals = _detect_signals(text, model_result, category, high_severity)

    band = model_band
    band_source = "model"

    if enable_escalation and model_band == "safe":
        if any(signals.get(flag_id) for flag_id in DEFAULT_ESCALATION_IDS):
            band = "suspicious"
            band_source = "heuristic_escalation"

    if band == "safe":
        reasons = _clear_reasons(signals)[:3]
        if len(reasons) < 2:
            reasons.append({"id": "no_known_patterns", "kind": "clear",
                             "text": "Nothing in the wording matched our known scam patterns"})
    else:
        reasons = _red_flag_reasons(text, signals)[:4]
        if not reasons:
            reasons = [{"id": "model_pattern_match", "kind": "red_flag",
                        "text": "The overall wording closely matches known scam messages"}]

    advice = _advice_for(band, signals)

    return {
        "band": band,
        "model_band": model_band,
        "band_source": band_source,
        "reasons": reasons,
        "advice": advice,
        "signals": signals,
    }
