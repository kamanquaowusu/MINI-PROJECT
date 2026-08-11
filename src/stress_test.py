"""
stress_test.py

Measures how much of the baseline's "perfect" score comes from surface
giveaways rather than real understanding of scams.

Method:
  1. Retrain the exact same TF-IDF + LogReg baseline on train.
  2. Evaluate on the ORIGINAL test set (should reproduce ~1.000).
  3. Evaluate again on a NEUTRALISED test set where the class-giveaway
     tokens are blanked out in BOTH classes:
        - URLs and <URL> placeholders
        - phone numbers and <PHONE> placeholders
        - dates like 2026-02-07
        - the words "balance" and "confirmed"
     If the score stays near 1.000, the leak runs even deeper.
     If it collapses, that gap is the amount of "performance" that was
     really just the model reading the generator's fingerprints.

This does NOT fix the dataset. It quantifies the problem so you can
report it honestly.
"""

import re
import numpy as np
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import precision_recall_fscore_support, roc_auc_score

DATA_DIR = "/home/claude/momo_project"

train = pd.read_csv(f"{DATA_DIR}/train.csv")
test = pd.read_csv(f"{DATA_DIR}/test.csv")
for d in (train, test):
    d["normalized_text"] = d["normalized_text"].fillna("")

y_train, y_test = train["label"].values, test["label"].values


# ---------------------------------------------------------------------------
# The "neutraliser": blank out the tokens we found leaking, in BOTH classes.
# ---------------------------------------------------------------------------
RE_URL = re.compile(r"https?://\S+|www\.\S+|<url>", re.I)
RE_PHONE = re.compile(r"\b0\d{9}\b|<phone>", re.I)
RE_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")
RE_GIVEAWAY_WORDS = re.compile(r"\b(balance|confirmed)\b", re.I)


def neutralise(text: str) -> str:
    s = str(text)
    s = RE_URL.sub(" ", s)
    s = RE_PHONE.sub(" ", s)
    s = RE_DATE.sub(" ", s)
    s = RE_GIVEAWAY_WORDS.sub(" ", s)
    s = re.sub(r"\s+", " ", s).strip()
    return s


# ---------------------------------------------------------------------------
# Train the baseline once (same recipe as baseline.py).
# ---------------------------------------------------------------------------
word_vec = TfidfVectorizer(analyzer="word", ngram_range=(1, 2), min_df=2, sublinear_tf=True)
char_vec = TfidfVectorizer(analyzer="char_wb", ngram_range=(3, 5), min_df=2, sublinear_tf=True)

Xtr = hstack([word_vec.fit_transform(train["normalized_text"]),
              char_vec.fit_transform(train["normalized_text"])]).tocsr()

clf = LogisticRegression(max_iter=2000, C=4.0, class_weight="balanced")
clf.fit(Xtr, y_train)


def score(texts, y_true, label):
    X = hstack([word_vec.transform(texts), char_vec.transform(texts)]).tocsr()
    proba = clf.predict_proba(X)[:, 1]
    pred = (proba >= 0.5).astype(int)
    p, r, f1, _ = precision_recall_fscore_support(
        y_true, pred, labels=[1], average="binary", zero_division=0)
    acc = (pred == y_true).mean()
    auc = roc_auc_score(y_true, proba)
    print(f"\n[{label}]")
    print(f"  accuracy={acc:.3f}  phishing precision={p:.3f}  recall={r:.3f}  f1={f1:.3f}  ROC-AUC={auc:.3f}")
    return acc, f1


# ---------------------------------------------------------------------------
# Compare: original test vs neutralised test (same trained model).
# ---------------------------------------------------------------------------
print("=" * 55)
print("STRESS TEST: how much of the score is a data artifact?")
print("=" * 55)

acc_orig, f1_orig = score(test["normalized_text"], y_test, "ORIGINAL test set")

test_neut = test["normalized_text"].apply(neutralise)
acc_neut, f1_neut = score(test_neut, y_test, "NEUTRALISED test set (giveaways blanked)")

print("\n" + "=" * 55)
print("INTERPRETATION")
print("=" * 55)
print(f"Accuracy dropped from {acc_orig:.3f} to {acc_neut:.3f} "
      f"(a drop of {acc_orig - acc_neut:.3f}).")
print(f"Phishing-F1 dropped from {f1_orig:.3f} to {f1_neut:.3f} "
      f"(a drop of {f1_orig - f1_neut:.3f}).")
print()
if acc_orig - acc_neut < 0.02:
    print("Small drop -> the giveaways are NOT the only leak; the two classes")
    print("differ in even more ways. The dataset needs deeper rebalancing.")
else:
    print("Large drop -> a big chunk of the 'perfect' score came purely from")
    print("those surface tokens. That gap is the size of the shortcut the model")
    print("was exploiting instead of learning what makes a message a scam.")

# Show a couple of before/after examples so the effect is concrete.
print("\nExamples (before -> after neutralising):")
for i in test.sample(3, random_state=7).index:
    before = test.loc[i, "normalized_text"][:90]
    after = neutralise(test.loc[i, "normalized_text"])[:90]
    print(f"  label={test.loc[i,'label']}")
    print(f"    before: {before}")
    print(f"    after:  {after}")
