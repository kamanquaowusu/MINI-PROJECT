"""
shadow_report.py

Run with: python -m api.shadow_report

Prints the shadow-mode validation summary -- band counts, consent rate, and
a model-implied-vs-user-confirmed confusion matrix with precision/recall.
This is the concrete artifact for the project PDF's Section 8.4 "periodically
compare model bands against user-confirmed outcomes" requirement. It is
pilot data from a handful of manual demo interactions, not a validated
benchmark -- treat it accordingly.
"""

from api import store


def main():
    s = store.summary()

    print("=" * 55)
    print("SHADOW-MODE SUMMARY (pilot data, not a validated benchmark)")
    print("=" * 55)
    print("checks_total :", s["checks_total"])
    print("consented    :", s["consented"])
    print("by_band      :", s["by_band"])
    print("feedback_total:", s["feedback_total"])
    print()

    if s["confusion"] is None:
        print("No feedback with a derivable label yet -- confusion matrix empty.")
        return

    c = s["confusion"]
    print("Confusion matrix (model-implied label vs. user-confirmed label):")
    print(f"  tp={c['tp']}  fp={c['fp']}  tn={c['tn']}  fn={c['fn']}")
    print(f"precision: {s['precision']}")
    print(f"recall   : {s['recall']}")


if __name__ == "__main__":
    main()
