import os
import pandas as pd
from preprocessor import MessagePreprocessor


def preprocess_and_save():
    input_path = "dataset/raw/messages.csv"
    output_dir = "dataset/processed"
    output_path = os.path.join(output_dir, "preprocessed_messages.csv")

    # 1. Check if raw dataset exists
    if not os.path.exists(input_path):
        print(f"Error: Raw dataset file not found at '{input_path}'")
        return

    print(f"Loading raw dataset from '{input_path}'...")
    raw_df = pd.read_csv(input_path)

    # 2. Run Preprocessor
    preprocessor = MessagePreprocessor()
    print("Running text normalization and metadata extraction...")
    processed_df = preprocessor.process_dataframe(raw_df, text_column="text")

    # 3. Create output directory if it doesn't exist
    os.makedirs(output_dir, exist_ok=True)

    # 4. Save processed dataset
    processed_df.to_csv(output_path, index=False)
    print(f"\nSuccessfully saved preprocessed dataset to '{output_path}'")

    # 5. Display Summary Statistics
    print("\n--- PREPROCESSING SUMMARY ---")
    print(f"Total rows processed: {len(processed_df)}")
    print(f"Columns in output dataset ({len(processed_df.columns)}):")
    print(list(processed_df.columns))

    print("\n--- METADATA FEATURE DISTRIBUTION ---")
    print(f"Messages with URLs      : {processed_df['has_url'].sum()}")
    print(f"Messages with Currency  : {processed_df['has_currency'].sum()}")
    print(f"Messages with Mentions  : {processed_df['has_mention'].sum()}")
    print(f"Messages with Shouting  : {processed_df['is_shouting'].sum()}")

    print("\n--- SAMPLE ROW COMPARISON ---")
    sample = processed_df.iloc[0]
    print(f"Original Text   : {sample['text']}")
    print(f"Normalized Text : {sample['normalized_text']}")


if __name__ == "__main__":
    preprocess_and_save()