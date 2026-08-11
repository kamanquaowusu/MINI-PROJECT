"""
baseline.py

A strong, fast, interpretable baseline for the MoMo phishing detector.

It does NOT use a transformer. It uses:
  - TF-IDF features (word n-grams + character n-grams) on normalized_text
  - Logistic Regression and Linear SVM
and evaluates them properly:
  - precision / recall / F1 on the PHISHING class specifically
  - full classification report + confusion matrix
  - per-category breakdown (where is the model weak?)

Reads train.csv / val.csv / test.csv, trains on train, tunes the decision
threshold on val, reports final numbers on test.
"""

import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import (
    classification_report, confusion_matrix,
    precision_recall_fscore_support, roc_auc_score, average_precision_score,
)

DATA_DIR = "/home/claude/momo_project"

train = pd.read_csv(f"{DATA_DIR}/train.csv")
val = pd.read_csv(f"{DATA_DIR}/val.csv")
test = pd.read_csv(f"{DATA_DIR}/test.csv")

# Use normalized_text as the model input (obfuscation already folded out).
for d in (train, val, test):
    d["normalized_text"] = d["normalized_text"].fillna("")

y_train, y_val, y_test = train["label"].values, val["label"].values, test["label"].values


# ---------------------------------------------------------------------------
# STEP 1: build TF-IDF features
# ---------------------------------------------------------------------------
# Two vectorizers:
#   - word-level (1-2 grams): captures phrases like "verify your pin"
#   - char-level (3-5 grams): catches code-switched Twi tokens and leftover
#     obfuscation residue that word tokenization would miss
word_vec = TfidfVectorizer(
    analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True,
)
char_vec = TfidfVectorizer(
    analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True,
)

# Fit ONLY on training text, then transform all splits (never fit on val/test).
Xtr_word = word_vec.fit_transform(train["normalized_text"])
Xtr_char = char_vec.fit_transform(train["normalized_text"])
Xtr = hstack([Xtr_word, Xtr_char]).tocsr()

Xval = hstack([word_vec.transform(val["normalized_text"]),
               char_vec.transform(val["normalized_text"])]).tocsr()
Xte = hstack([word_vec.transform(test["normalized_text"]),
              char_vec.transform(test["normalized_text"])]).tocsr()

print(f"Feature matrix: {Xtr.shape[1]} features "
      f"({Xtr_word.shape[1]} word + {Xtr_char.shape[1]} char)")


# ---------------------------------------------------------------------------
# STEP 2: train two models
# ---------------------------------------------------------------------------
# class_weight='balanced' handles the mild imbalance without synthetic data.
logreg = LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")
logreg.fit(Xtr, y_train)

# LinearSVC has no predict_proba, so wrap it to get calibrated probabilities.
svm = CalibratedClassifierCV(
    LinearSVC(C=1.0, class_weight="balanced"), cv=3
)
svm.fit(Xtr, y_train)


def evaluate(model, X, y_true, name, threshold=0.5):
    proba = model.predict_proba(X)[:, 1]
    y_pred = (proba >= threshold).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, y_pred, labels=[1], average="binary", zero_division=0
    )
    auc = roc_auc_score(y_true, proba)
    ap = average_precision_score(y_true, proba)
    print(f"\n[{name}] (threshold={threshold:.2f})")
    print(f"  phishing  precision={p:.3f}  recall={r:.3f}  f1={f1:.3f}")
    print(f"  ROC-AUC={auc:.3f}  PR-AUC={ap:.3f}")
    return proba, y_pred, f1


# ---------------------------------------------------------------------------
# STEP 3: pick the better model on validation, then tune its threshold on val
# ---------------------------------------------------------------------------
print("\n=== Validation (default threshold 0.5) ===")
_, _, f1_lr = evaluate(logreg, Xval, y_val, "LogReg  val")
_, _, f1_sv = evaluate(svm, Xval, y_val, "LinSVM  val")

best_model, best_name = (logreg, "LogReg") if f1_lr >= f1_sv else (svm, "LinSVM")
print(f"\nBest model on val: {best_name}")

# Sweep thresholds on VALIDATION only, choose the one with best phishing-F1.
val_proba = best_model.predict_proba(Xval)[:, 1]
best_t, best_val_f1 = 0.5, -1
for t in np.arange(0.20, 0.81, 0.02):
    pred = (val_proba >= t).astype(int)
    _, _, f1, _ = precision_recall_fscore_support(
        y_val, pred, labels=[1], average="binary", zero_division=0
    )
    if f1 > best_val_f1:
        best_val_f1, best_t = f1, t
print(f"Best threshold on val: {best_t:.2f} (val phishing-F1={best_val_f1:.3f})")


# ---------------------------------------------------------------------------
# STEP 4: FINAL evaluation on test, using the threshold chosen on val
# ---------------------------------------------------------------------------
print("\n" + "=" * 50)
print("FINAL TEST RESULTS")
print("=" * 50)
test_proba, test_pred, _ = evaluate(
    best_model, Xte, y_test, f"{best_name} TEST", threshold=best_t
)

print("\nFull classification report (test):")
print(classification_report(y_test, test_pred,
                            target_names=["legitimate", "phishing"],
                            digits=3))

print("Confusion matrix (test), rows=true, cols=pred:")
print("              pred_legit  pred_phish")
cm = confusion_matrix(y_test, test_pred)
print(f"true_legit    {cm[0,0]:>10}  {cm[0,1]:>10}")
print(f"true_phish    {cm[1,0]:>10}  {cm[1,1]:>10}")


# ---------------------------------------------------------------------------
# STEP 5: per-category breakdown -- where does the model fail?
# ---------------------------------------------------------------------------
# For phishing rows, group by category and see recall (fraction caught).
test_eval = test.copy()
test_eval["pred"] = test_pred
phish = test_eval[test_eval["label"] == 1]
print("\nRecall by scam category (fraction of scams caught):")
recall_by_cat = phish.groupby("category")["pred"].mean().sort_values()
for cat, rec in recall_by_cat.items():
    n = (phish["category"] == cat).sum()
    print(f"  {cat:<24} {rec:.3f}   (n={n})")


# ---------------------------------------------------------------------------
# STEP 6: interpretability -- top phishing-indicative word features
# ---------------------------------------------------------------------------
if best_name == "LogReg":
    feat_names = np.array(word_vec.get_feature_names_out().tolist()
                          + char_vec.get_feature_names_out().tolist())
    coefs = logreg.coef_[0]
    top_phish = np.argsort(coefs)[-20:][::-1]
    top_legit = np.argsort(coefs)[:20]
    print("\nTop 20 features pushing toward PHISHING:")
    print(", ".join(repr(feat_names[i]) for i in top_phish))
    print("\nTop 20 features pushing toward LEGITIMATE:")
    print(", ".join(repr(feat_names[i]) for i in top_legit))

print("\nDone.")
