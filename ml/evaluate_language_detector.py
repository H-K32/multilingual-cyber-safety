
import os
import pandas as pd
from language_detector import UnicodeLanguageDetector


def evaluate_language_detection():
    input_path = "dataset/processed/preprocessed_messages.csv"

    if not os.path.exists(input_path):
        print(f"Error: Dataset not found at '{input_path}'. Run preprocess_dataset.py first.")
        return

    df = pd.read_csv(input_path)
    detector = UnicodeLanguageDetector(min_letters=3, minor_script_threshold=0.08)

    print("Running language detection on preprocessed dataset...")
    detected_df = detector.process_dataframe(df, text_column="text")

    # 1. Compare detected_language vs ground-truth language
    correct_lang = (detected_df["detected_language"] == detected_df["language"]).sum()
    total_rows = len(detected_df)
    lang_accuracy = (correct_lang / total_rows) * 100

    # 2. Compare is_code_switched vs ground-truth code_switched
    correct_cs = (detected_df["is_code_switched"] == detected_df["code_switched"]).sum()
    cs_accuracy = (correct_cs / total_rows) * 100

    print("\n--- LANGUAGE DETECTION EVALUATION RESULTS ---")
    print(f"Total Messages Evaluated: {total_rows}")
    print(f"Language Detection Accuracy     : {correct_lang}/{total_rows} ({lang_accuracy:.2f}%)")
    print(f"Code-Switching Detection Accuracy: {correct_cs}/{total_rows} ({cs_accuracy:.2f}%)")

    # 3. Print Breakdown per Language Class
    print("\n--- CONFUSION MATRIX (Ground Truth vs Detected) ---")
    crosstab = pd.crosstab(
        detected_df["language"],
        detected_df["detected_language"],
        margins=True,
        margins_name="Total",
    )
    print(crosstab)

    # 4. Show Misclassifications (if any exist)
    mismatches = detected_df[detected_df["detected_language"] != detected_df["language"]]

    if not mismatches.empty:
        print(f"\n--- MISCLASSIFIED MESSAGES ({len(mismatches)}) ---")
        for idx, row in mismatches.iterrows():
            print(f"ID              : {row['id']}")
            print(f"Text            : {row['text']}")
            print(f"Ground Truth    : Language={row['language']} | Code-Switched={row['code_switched']}")
            print(f"Detected        : Language={row['detected_language']} | Ethiopic={row['ethiopic_ratio']} | Latin={row['latin_ratio']}")
            print("-" * 60)
    else:
        print("\nAll messages were correctly classified according to ground-truth script labels!")


if __name__ == "__main__":
    evaluate_language_detection()