"""
triage_model.py

Turns the two-class (legitimate / scam) data into a THREE-TIER risk classifier:
    safe  |  suspicious  |  dangerous

Logic (Option A + Option B):
  1. Train a calibrated classifier that outputs a real probability that a
     message is a scam.
  2. Cut that probability into three bands with two thresholds chosen on
     the validation set to satisfy a stated policy.
  3. Apply a severity override: high-confidence scams whose category is
     "asks for money / account action" are forced to 'dangerous'.

Outputs a report and saves the trained pieces so the same logic can be
reused on better data later.
"""

import re
import numpy as np
import pandas as pd
import joblib
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import precision_recall_fscore_support, classification_report

DATA_DIR = "/home/claude/momo_project"

train = pd.read_csv(f"{DATA_DIR}/train.csv")
val = pd.read_csv(f"{DATA_DIR}/val.csv")
test = pd.read_csv(f"{DATA_DIR}/test.csv")
for d in (train, val, test):
    d["normalized_text"] = d["normalized_text"].fillna("")
    d["category"] = d["category"].fillna("unknown")

y_train, y_val, y_test = train["label"].values, val["label"].values, test["label"].values


# ---------------------------------------------------------------------------
# STEP 1-3: features + calibrated classifier (calibrated = trustworthy probs)
# ---------------------------------------------------------------------------
word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)

Xtr = hstack([word_vec.fit_transform(train["normalized_text"]),
              char_vec.fit_transform(train["normalized_text"])]).tocsr()
Xval = hstack([word_vec.transform(val["normalized_text"]),
               char_vec.transform(val["normalized_text"])]).tocsr()
Xte = hstack([word_vec.transform(test["normalized_text"]),
              char_vec.transform(test["normalized_text"])]).tocsr()

# Calibrated logistic regression: the calibration step makes predict_proba
# output honest probabilities, which the 3-band cut depends on.
base = LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")
clf = CalibratedClassifierCV(base, method="isotonic", cv=5)
clf.fit(Xtr, y_train)

val_proba = clf.predict_proba(Xval)[:, 1]
test_proba = clf.predict_proba(Xte)[:, 1]


# ---------------------------------------------------------------------------
# STEP 4: choose two thresholds on VALIDATION to meet a stated policy.
#   - dangerous cut (T_HIGH): lowest prob such that precision-of-scam >= 0.95
#   - safe cut     (T_LOW):  highest prob such that among msgs below it,
#                            at least 99% are truly legitimate
# ---------------------------------------------------------------------------
def scam_precision_above(threshold, proba, y):
    flagged = proba >= threshold
    if flagged.sum() == 0:
        return 1.0
    return y[flagged].mean()          # fraction of flagged that are truly scam

def legit_purity_below(threshold, proba, y):
    passed = proba < threshold
    if passed.sum() == 0:
        return 1.0
    return (y[passed] == 0).mean()    # fraction of passed that are truly legit

TARGET_DANGER_PRECISION = 0.95
TARGET_SAFE_PURITY = 0.99

grid = np.round(np.arange(0.01, 1.00, 0.01), 2)

# T_HIGH: smallest threshold whose scam-precision meets target (maximise recall)
t_high_candidates = [t for t in grid
                     if scam_precision_above(t, val_proba, y_val) >= TARGET_DANGER_PRECISION]
T_HIGH = min(t_high_candidates) if t_high_candidates else 0.70

# T_LOW: largest threshold whose "below" region stays >=99% legit (maximise safe volume)
t_low_candidates = [t for t in grid
                    if legit_purity_below(t, val_proba, y_val) >= TARGET_SAFE_PURITY and t < T_HIGH]
T_LOW = max(t_low_candidates) if t_low_candidates else 0.20

print("=" * 55)
print("CHOSEN THRESHOLDS (from validation)")
print("=" * 55)
print(f"  safe   : scam-probability <  {T_LOW:.2f}")
print(f"  suspic.: {T_LOW:.2f} <= scam-probability < {T_HIGH:.2f}")
print(f"  danger : scam-probability >= {T_HIGH:.2f}")


# ---------------------------------------------------------------------------
# STEP 5: severity override map (Option B, documented policy).
# Categories that involve money movement / credential requests are treated
# as high-severity: if the model already thinks it's fairly likely a scam,
# push it to 'dangerous' even if it sat in the suspicious band.
# ---------------------------------------------------------------------------
HIGH_SEVERITY_CATEGORIES = {
    "reversal", "wrong_send", "banking", "impersonation",
    "account_verification", "loan_scam",
}
SEVERITY_OVERRIDE_MIN_PROB = 0.50   # only override when model isn't confidently-safe

def assign_band(proba, category):
    if proba >= T_HIGH:
        return "dangerous"
    if proba < T_LOW:
        return "safe"
    # middle band: apply severity override
    if category in HIGH_SEVERITY_CATEGORIES and proba >= SEVERITY_OVERRIDE_MIN_PROB:
        return "dangerous"
    return "suspicious"


# ---------------------------------------------------------------------------
# STEP 6: apply to TEST and report band-vs-truth
# ---------------------------------------------------------------------------
test_bands = [assign_band(p, c) for p, c in zip(test_proba, test["category"])]
test = test.assign(scam_proba=test_proba, band=test_bands)

print("\n" + "=" * 55)
print("BAND ASSIGNMENTS ON TEST SET")
print("=" * 55)
print("\nHow many messages landed in each band:")
print(test["band"].value_counts().reindex(["safe", "suspicious", "dangerous"]).fillna(0).astype(int))

print("\nWhat each band actually contained (truth: 0=legit, 1=scam):")
crosstab = pd.crosstab(test["band"], test["label"],
                       rownames=["band"], colnames=["truth"]).reindex(
                       ["safe", "suspicious", "dangerous"]).fillna(0).astype(int)
crosstab.columns = ["legit(0)", "scam(1)"]
print(crosstab)

# The numbers that matter for a triage system:
for band in ["safe", "suspicious", "dangerous"]:
    sub = test[test["band"] == band]
    if len(sub) == 0:
        print(f"\n{band}: (empty)")
        continue
    scam_frac = sub["label"].mean()
    print(f"\n{band}: {len(sub)} messages, {scam_frac:.1%} truly scam")


# ---------------------------------------------------------------------------
# STEP 7: reality check -- probability histogram (is the middle band empty?)
# ---------------------------------------------------------------------------
print("\n" + "=" * 55)
print("PROBABILITY DISTRIBUTION (reality check)")
print("=" * 55)
bins = [0, .05, .1, .2, .3, .4, .5, .6, .7, .8, .9, .95, 1.01]
hist = pd.cut(test_proba, bins=bins, right=False).value_counts().sort_index()
for interval, cnt in hist.items():
    bar = "#" * int(60 * cnt / max(hist.max(), 1))
    print(f"  [{interval.left:.2f},{interval.right:.2f})  {cnt:>5}  {bar}")

mid = ((test_proba >= T_LOW) & (test_proba < T_HIGH)).mean()
print(f"\nFraction of test messages in the raw middle zone "
      f"[{T_LOW:.2f},{T_HIGH:.2f}): {mid:.1%}")
if mid < 0.05:
    print("-> The middle is nearly empty: the model is over-confident (the known")
    print("   synthetic-data artifact). On real data this band would fill in.")


# ---------------------------------------------------------------------------
# Save the trained pieces so the SAME logic runs on better data later.
# ---------------------------------------------------------------------------
joblib.dump({
    "word_vec": word_vec, "char_vec": char_vec, "clf": clf,
    "T_LOW": T_LOW, "T_HIGH": T_HIGH,
    "HIGH_SEVERITY_CATEGORIES": HIGH_SEVERITY_CATEGORIES,
    "SEVERITY_OVERRIDE_MIN_PROB": SEVERITY_OVERRIDE_MIN_PROB,
}, f"{DATA_DIR}/triage_model.joblib")
print(f"\nSaved model + thresholds to {DATA_DIR}/triage_model.joblib")

# Save the test set with its bands for inspection.
test[["text", "category", "label", "scam_proba", "band"]].to_csv(
    f"{DATA_DIR}/test_with_bands.csv", index=False)
print(f"Saved banded test predictions to {DATA_DIR}/test_with_bands.csv")
