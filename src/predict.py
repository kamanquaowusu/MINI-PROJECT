"""
predict.py

Inference wrapper for the three-tier MoMo smishing triage model.

Given a RAW sms string, it:
  1. normalises it (NFKC + confusable folding + invisible-char stripping)
     -- the model was trained on normalised text, so raw input must be
        normalised the same way or predictions are meaningless
  2. vectorises it with the fitted TF-IDF vectorisers
  3. gets a calibrated scam-probability from the saved classifier
  4. maps that probability (plus a category severity override) to a band:
        safe | suspicious | dangerous

Usage:
    from predict import TriageClassifier
    clf = TriageClassifier("models/triage_model.joblib")
    result = clf.classify("Dear customer, your MoMo was reversed. Refund now: bit.ly/x")
    # -> {"band": "...", "scam_probability": 0.97, "reasons": [...]}

NOTE: this model is trained on SYNTHETIC data and is NOT yet validated on
real messages. Treat outputs as advisory only until a real-world evaluation
set confirms performance. See the documentation's Limitations section.
"""

import joblib
from scipy.sparse import hstack

try:
    # Your existing obfuscation-defence module.
    from normalize import normalize_message
except Exception:
    normalize_message = None


class TriageClassifier:
    def __init__(self, model_path="models/triage_model.joblib"):
        bundle = joblib.load(model_path)
        self.word_vec = bundle["word_vec"]
        self.char_vec = bundle["char_vec"]
        self.clf = bundle["clf"]
        self.T_LOW = bundle["T_LOW"]
        self.T_HIGH = bundle["T_HIGH"]
        self.HIGH_SEVERITY = bundle["HIGH_SEVERITY_CATEGORIES"]
        self.OVERRIDE_MIN = bundle["SEVERITY_OVERRIDE_MIN_PROB"]

    def _normalise(self, raw_text):
        """Return (normalized_text, obfuscation_flags)."""
        if normalize_message is not None:
            out = normalize_message(raw_text)
            # normalize_message is expected to return a dict with these keys;
            # fall back gracefully if the shape differs.
            if isinstance(out, dict):
                return out.get("normalized_text", raw_text), {
                    "had_confusable": out.get("had_confusable", False),
                    "had_invisible_char": out.get("had_invisible_char", False),
                    "obfuscation_suspected": out.get("obfuscation_suspected", False),
                }
        # Fallback: no normaliser available -> use raw text, no flags.
        return raw_text, {"had_confusable": False,
                          "had_invisible_char": False,
                          "obfuscation_suspected": False}

    def classify(self, raw_text, category="unknown"):
        norm_text, flags = self._normalise(raw_text)

        X = hstack([self.word_vec.transform([norm_text]),
                    self.char_vec.transform([norm_text])]).tocsr()
        proba = float(self.clf.predict_proba(X)[:, 1][0])

        reasons = []
        if proba >= self.T_HIGH:
            band = "dangerous"
            reasons.append(f"high scam probability ({proba:.2f})")
        elif proba < self.T_LOW:
            band = "safe"
            reasons.append(f"low scam probability ({proba:.2f})")
        else:
            band = "suspicious"
            reasons.append(f"uncertain scam probability ({proba:.2f})")
            if category in self.HIGH_SEVERITY and proba >= self.OVERRIDE_MIN:
                band = "dangerous"
                reasons.append(f"severity override: high-risk category '{category}'")

        if flags["obfuscation_suspected"]:
            reasons.append("obfuscation detected (hidden/look-alike characters)")

        return {
            "band": band,
            "scam_probability": round(proba, 4),
            "obfuscation_suspected": flags["obfuscation_suspected"],
            "reasons": reasons,
            "advisory_only": True,   # model not yet validated on real data
        }


if __name__ == "__main__":
    clf = TriageClassifier("models/triage_model.joblib")
    samples = [
        "Confirmed. You have received GHS50.00 from KWAME. Your new balance is GHS212.30.",
        "URGENT: Your MoMo wallet is blocked. Verify your PIN now at momo-verify.gh to unlock.",
        "You have WON GHS5,000 in the MTN promo! Send GHS20 to claim your prize now.",
    ]
    for s in samples:
        r = clf.classify(s)
        print(f"[{r['band'].upper():<10}] p={r['scam_probability']:.2f}  {s[:60]}")
