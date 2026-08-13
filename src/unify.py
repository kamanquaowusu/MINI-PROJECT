"""
unify.py

Reads the four raw files and produces ONE clean table: unified_sms.csv

What it does, in order:
  1. Load momo_sms_dataset_v2.jsonl        -> main training data
  2. Load the CSV, keep SMS rows only      -> extra training data
  3. Load the *_generated file, but only keep rows whose normalized_text
     we haven't already seen (avoids near-duplicate leakage)
  4. Leave obfuscation_validation_set.jsonl completely alone -- it is not
     touched by this script at all, on purpose.

Every kept row ends up with these columns, no matter which file it came from:
  text, normalized_text, label, category, mechanism, source_file
"""

import json
import re
import pandas as pd

UPLOAD_DIR = "data/raw"
OUTPUT_PATH = "data/processed/unified_sms.csv"

# Every row's normalized_text we've already added, so file 3 can check
# against it before adding anything.
seen_normalized_texts = set()

all_rows = []


def add_row(text, normalized_text, label, category, mechanism, source_file):
    """Add one row to the running list, and remember its normalized text."""
    if normalized_text is None or normalized_text == "":
        normalized_text = text  # fallback if a file has no normalized_text
    all_rows.append({
        "text": text,
        "normalized_text": normalized_text,
        "label": label,           # 0 = legitimate, 1 = phishing/scam
        "category": category,
        "mechanism": mechanism,
        "source_file": source_file,
    })
    seen_normalized_texts.add(normalized_text)


# ---------------------------------------------------------------------------
# STEP 1: momo_sms_dataset_v2.jsonl  (main file, keep everything)
# ---------------------------------------------------------------------------
print("Loading momo_sms_dataset_v2.jsonl ...")
count_v2 = 0
with open(f"{UPLOAD_DIR}/momo_sms_dataset_v2.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)

        # row["label"] is the string "legitimate" or "illegitimate" ->
        # turn it into 0 / 1
        label = 0 if row["label"] == "legitimate" else 1

        add_row(
            text=row["text"],
            normalized_text=row.get("normalized_text"),
            label=label,
            category=row.get("category", "unknown"),
            mechanism=row.get("mechanism", "unknown"),
            source_file="v2",
        )
        count_v2 += 1
print(f"  added {count_v2} rows from v2")


# ---------------------------------------------------------------------------
# STEP 2: ghana_momo_phishing_dataset_synthetic_1000.csv (SMS rows only)
# ---------------------------------------------------------------------------
print("Loading ghana_momo_phishing_dataset_synthetic_1000.csv ...")
df_csv = pd.read_csv(f"{UPLOAD_DIR}/ghana_momo_phishing_dataset_synthetic_1000.csv")

# Keep only SMS rows -- we're building an SMS-only classifier for now.
df_csv_sms = df_csv[df_csv["channel"] == "SMS"]

count_csv = 0
for _, row in df_csv_sms.iterrows():
    # Here label is the string "legitimate" or "phishing"
    label = 0 if row["label"] == "legitimate" else 1

    add_row(
        text=row["message_text"],
        normalized_text=None,          # this file has no normalized_text column
        label=label,
        category=row["scam_type"],     # this file calls it scam_type, not category
        mechanism="unknown",           # this file has no mechanism column
        source_file="csv",
    )
    count_csv += 1
print(f"  added {count_csv} SMS rows from csv "
      f"(dropped {len(df_csv) - len(df_csv_sms)} Email rows)")


# ---------------------------------------------------------------------------
# STEP 3: momo_sms_dataset_generated.jsonl (only NEW rows, dedup by text)
# ---------------------------------------------------------------------------
print("Loading momo_sms_dataset_generated.jsonl ...")
count_gen_added = 0
count_gen_skipped = 0
with open(f"{UPLOAD_DIR}/momo_sms_dataset_generated.jsonl", encoding="utf-8") as f:
    for line in f:
        line = line.strip()
        if not line:
            continue
        row = json.loads(line)

        # This file has no normalized_text column, so we compare on raw text.
        text = row["text"]
        if text in seen_normalized_texts:
            count_gen_skipped += 1
            continue

        label = 0 if row["label"] == "legitimate" else 1

        add_row(
            text=text,
            normalized_text=None,
            label=label,
            category=row.get("category", "unknown"),
            mechanism="unknown",       # this file has no mechanism column
            source_file="generated_v1",
        )
        count_gen_added += 1
print(f"  added {count_gen_added} new rows, skipped {count_gen_skipped} duplicates")


# ---------------------------------------------------------------------------
# STEP 4: safe_dataset_redacted.csv -- genuine bank/telco service
# notifications (CBG, MTN, T-Cash, Stanbic, etc.), all legitimate.
# Hard negatives: teaches the model that "banking"/"ATM"/"security"
# language isn't itself a scam signal, to cut false positives.
# Dedup by raw text (no normalized_text column, and the file itself has
# internal exact repeats).
# ---------------------------------------------------------------------------
print("Loading safe_dataset_redacted.csv ...")
df_safe = pd.read_csv(f"{UPLOAD_DIR}/safe_dataset_redacted.csv")

# This export splits some real SMS into two rows: a bare salutation
# ("Dear Customer," / "Dear [REDACTED],") followed by the message body as
# the next row from the same sender. Trained separately, the salutation
# row is a near-content-free fragment and the body row is missing its
# opening -- neither looks like a real SMS. Recombine them first.
SALUTATION_RE = re.compile(r"^Dear (Customer|\[REDACTED\]),?$")
safe_texts = []
i = 0
rows_safe = df_safe.to_dict("records")
while i < len(rows_safe):
    msg = str(rows_safe[i]["message"])
    if (SALUTATION_RE.match(msg.strip())
            and i + 1 < len(rows_safe)
            and rows_safe[i + 1]["sender"] == rows_safe[i]["sender"]):
        safe_texts.append(f"{msg} {rows_safe[i + 1]['message']}")
        i += 2
    else:
        safe_texts.append(msg)
        i += 1

count_safe_added = 0
count_safe_skipped = 0
for text in safe_texts:
    if text in seen_normalized_texts:
        count_safe_skipped += 1
        continue

    add_row(
        text=text,
        normalized_text=None,
        label=0,                    # confirmed: every row is a legitimate notice
        category="legitimate",
        mechanism="unknown",
        source_file="safe_dataset_redacted",
    )
    count_safe_added += 1
print(f"  merged {len(df_safe) - len(safe_texts)} salutation fragments into their message body")
print(f"  added {count_safe_added} new rows, skipped {count_safe_skipped} duplicates")


# ---------------------------------------------------------------------------
# STEP 5: obfuscation_validation_set.jsonl -- deliberately NOT loaded here.
# It stays untouched in data/raw for a separate evaluation script.
# ---------------------------------------------------------------------------
print("Skipping obfuscation_validation_set.jsonl on purpose (held-out test set)")


# ---------------------------------------------------------------------------
# Build the final table and save it
# ---------------------------------------------------------------------------
final_df = pd.DataFrame(all_rows)

print()
print("=== Summary ===")
print(f"Total rows: {len(final_df)}")
print()
print("Rows by source file:")
print(final_df["source_file"].value_counts())
print()
print("Label balance (0=legitimate, 1=phishing/scam):")
print(final_df["label"].value_counts())
print()
print("Category counts:")
print(final_df["category"].value_counts())
print()
print("Sample rows:")
print(final_df.sample(5, random_state=42)[["text", "label", "category", "source_file"]])

final_df.to_csv(OUTPUT_PATH, index=False)
print()
print(f"Saved unified table to {OUTPUT_PATH}")
