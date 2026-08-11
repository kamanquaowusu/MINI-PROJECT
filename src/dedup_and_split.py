"""
dedup_and_split.py

Takes unified_sms.csv and produces train.csv / val.csv / test.csv such that:
  - exact duplicate messages are removed
  - messages that share the same "skeleton" (same wording, different
    amounts/phone numbers/names) are NEVER split across train/val/test
  - the label balance (legitimate vs phishing) is kept similar across
    train/val/test

Output files go to /home/claude/momo_project/
"""

import re
import hashlib
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold

INPUT_PATH = "/home/claude/momo_project/unified_sms.csv"
OUT_DIR = "/home/claude/momo_project"

df = pd.read_csv(INPUT_PATH)
print(f"Loaded {len(df)} rows")


# ---------------------------------------------------------------------------
# STEP 1: exact-duplicate removal
# ---------------------------------------------------------------------------
# Some rows already have a normalized_text, some don't (we filled missing
# ones with the raw text back in unify.py). Either way, drop exact repeats,
# keeping the first occurrence.
before = len(df)
df = df.drop_duplicates(subset="normalized_text", keep="first").reset_index(drop=True)
print(f"Removed {before - len(df)} exact duplicate rows -> {len(df)} remain")


# ---------------------------------------------------------------------------
# STEP 2: build a "skeleton" for every row -- the message with all the
# changeable details blanked out, so near-duplicate templates are caught.
# ---------------------------------------------------------------------------
# Regexes for the kinds of details that change between otherwise-identical
# messages: money amounts, phone numbers, long digit strings (references,
# transaction IDs), and URLs.
RE_URL = re.compile(r"https?://\S+|www\.\S+")
RE_AMOUNT = re.compile(r"GH[S₵C¢]?\s?\d[\d,]*(\.\d+)?", re.IGNORECASE)
RE_PHONE = re.compile(r"\b0\d{9}\b")
RE_LONG_DIGITS = re.compile(r"\b\d{5,}\b")   # transaction IDs, reference numbers
RE_EXISTING_TAG = re.compile(r"<[A-Za-z_]+>")  # <ACCOUNT>, <AMOUNT>, <PHONE>, etc.
RE_TIME = re.compile(r"\b\d{1,2}:\d{2}(:\d{2})?\s?(AM|PM|am|pm)?\b")
RE_DATE = re.compile(r"\b\d{4}-\d{2}-\d{2}\b")


def make_skeleton(text: str) -> str:
    s = str(text)
    s = RE_EXISTING_TAG.sub("<X>", s)   # any file's own placeholders -> one tag
    s = RE_URL.sub("<X>", s)
    s = RE_AMOUNT.sub("<X>", s)
    s = RE_DATE.sub("<X>", s)
    s = RE_TIME.sub("<X>", s)
    s = RE_PHONE.sub("<X>", s)
    s = RE_LONG_DIGITS.sub("<X>", s)
    s = s.lower().strip()
    s = re.sub(r"\s+", " ", s)          # collapse repeated whitespace
    return s


df["skeleton"] = df["normalized_text"].apply(make_skeleton)

# Turn each unique skeleton into a short group id (a hash), so
# StratifiedGroupKFold has something simple to group on.
df["skeleton_id"] = df["skeleton"].apply(
    lambda s: hashlib.md5(s.encode("utf-8")).hexdigest()[:12]
)

n_unique_skeletons = df["skeleton_id"].nunique()
print(f"Found {n_unique_skeletons} unique skeletons across {len(df)} rows")
print("Rows per skeleton (top 10 most repeated):")
print(df["skeleton_id"].value_counts().head(10))


# ---------------------------------------------------------------------------
# STEP 3: group-aware, label-stratified split into train / val / test
# ---------------------------------------------------------------------------
# StratifiedGroupKFold keeps every group (skeleton_id) fully inside one
# fold, while still trying to keep the label balance even across folds.
# We use 5 folds so each fold is ~20%: 1 fold -> test, 1 fold -> val,
# the remaining 3 folds -> train (70/15/15 roughly).
sgkf = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)

folds = list(sgkf.split(df, df["label"], groups=df["skeleton_id"]))

# folds[0] gives (train_idx, holdout_idx) for the first split.
# Take fold 0's holdout as TEST, fold 1's holdout as VAL, rest as TRAIN.
test_idx = folds[0][1]
val_idx = folds[1][1]

# Make sure val and test don't overlap (they won't, since folds are
# disjoint by construction) and remove val/test rows from train.
all_idx = set(df.index)
train_idx = sorted(all_idx - set(test_idx) - set(val_idx))

train_df = df.loc[train_idx].reset_index(drop=True)
val_df = df.loc[val_idx].reset_index(drop=True)
test_df = df.loc[test_idx].reset_index(drop=True)

print()
print("=== Split sizes ===")
print(f"train: {len(train_df)} ({len(train_df)/len(df):.1%})")
print(f"val:   {len(val_df)} ({len(val_df)/len(df):.1%})")
print(f"test:  {len(test_df)} ({len(test_df)/len(df):.1%})")


# ---------------------------------------------------------------------------
# STEP 4: sanity checks -- these are the checks that actually matter
# ---------------------------------------------------------------------------
# 4a. No skeleton should appear in more than one split.
train_sk = set(train_df["skeleton_id"])
val_sk = set(val_df["skeleton_id"])
test_sk = set(test_df["skeleton_id"])

overlap_train_val = train_sk & val_sk
overlap_train_test = train_sk & test_sk
overlap_val_test = val_sk & test_sk

print()
print("=== Leakage check (should all be 0) ===")
print(f"skeletons in both train & val:  {len(overlap_train_val)}")
print(f"skeletons in both train & test: {len(overlap_train_test)}")
print(f"skeletons in both val & test:   {len(overlap_val_test)}")

assert len(overlap_train_val) == 0
assert len(overlap_train_test) == 0
assert len(overlap_val_test) == 0

# 4b. Label balance should be similar across splits.
print()
print("=== Label balance per split (1 = phishing/scam) ===")
for name, split_df in [("train", train_df), ("val", val_df), ("test", test_df)]:
    frac_phishing = split_df["label"].mean()
    print(f"{name}: {frac_phishing:.1%} phishing")


# ---------------------------------------------------------------------------
# STEP 5: save
# ---------------------------------------------------------------------------
# Drop the helper columns before saving -- they were only needed to build
# the split correctly, not for training itself.
cols_to_keep = ["text", "normalized_text", "label", "category", "mechanism", "source_file"]

train_df[cols_to_keep].to_csv(f"{OUT_DIR}/train.csv", index=False)
val_df[cols_to_keep].to_csv(f"{OUT_DIR}/val.csv", index=False)
test_df[cols_to_keep].to_csv(f"{OUT_DIR}/test.csv", index=False)

print()
print(f"Saved train.csv, val.csv, test.csv to {OUT_DIR}")
