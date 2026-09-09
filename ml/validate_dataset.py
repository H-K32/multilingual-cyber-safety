import pandas as pd

DATASET_PATH = "dataset/raw/messages.csv"

REQUIRED_COLUMNS = [
    "id",
    "text",
    "label",
    "language",
    "code_switched",
    "threat_type",
    "indicators",
    "source"
]


def validate_dataset():
    print("=" * 50)
    print("DATASET VALIDATION")
    print("=" * 50)

    df = pd.read_csv(DATASET_PATH)

    # 1. Check columns
    print("\n[1] Checking columns...")

    missing_columns = [
        column for column in REQUIRED_COLUMNS
        if column not in df.columns
    ]

    if missing_columns:
        print("ERROR: Missing columns:", missing_columns)
    else:
        print("OK: All required columns are present.")

    # 2. Check number of rows
    print("\n[2] Dataset size...")
    print(f"Rows: {len(df)}")
    print(f"Columns: {len(df.columns)}")

    # 3. Check duplicate IDs
    print("\n[3] Checking duplicate IDs...")

    duplicate_ids = df["id"].duplicated().sum()

    if duplicate_ids == 0:
        print("OK: No duplicate IDs.")
    else:
        print(f"WARNING: {duplicate_ids} duplicate IDs found.")

    # 4. Check duplicate messages
    print("\n[4] Checking duplicate messages...")

    duplicate_messages = df["text"].duplicated().sum()

    if duplicate_messages == 0:
        print("OK: No duplicate messages.")
    else:
        print(f"WARNING: {duplicate_messages} duplicate messages found.")

    # 5. Check missing values
    print("\n[5] Checking missing values...")

    missing = df.isnull().sum()

    print(missing)

    # 6. Label distribution
    print("\n[6] Label distribution...")
    print(df["label"].value_counts())

    # 7. Language distribution
    print("\n[7] Language distribution...")
    print(df["language"].value_counts())

    # 8. Threat type distribution
    print("\n[8] Threat type distribution...")
    print(df["threat_type"].value_counts())

    # 9. Source distribution
    print("\n[9] Source distribution...")
    print(df["source"].value_counts())

    print("\n" + "=" * 50)
    print("VALIDATION COMPLETE")
    print("=" * 50)


if __name__ == "__main__":
    validate_dataset()