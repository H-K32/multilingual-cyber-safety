import os
import joblib
import pandas as pd
from scipy.sparse import hstack
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.linear_model import LogisticRegression
from sklearn.metrics import classification_report, confusion_matrix
from sklearn.model_selection import train_test_split


def train_and_evaluate():
    input_path = "dataset/processed/preprocessed_messages.csv"
    models_dir = "models"

    if not os.path.exists(input_path):
        print(f"Error: Dataset not found at '{input_path}'. Run preprocess_dataset.py first.")
        return

    df = pd.read_csv(input_path)

    metadata_cols = [
        "has_url",
        "has_currency",
        "has_mention",
        "is_shouting",
        "suspicious_unicode_count",
    ]

    for col in metadata_cols:
        df[col] = df[col].astype(int)

    # Train/Test Split
    train_df, test_df = train_test_split(
        df, test_size=0.20, random_state=42, stratify=df["label"]
    )

    print(f"Dataset split: {len(train_df)} training samples, {len(test_df)} test samples.")

    # Vectorize Normalized Text
    vectorizer = TfidfVectorizer(ngram_range=(1, 2), max_features=100)
    X_train_text = vectorizer.fit_transform(train_df["normalized_text"])
    X_test_text = vectorizer.transform(test_df["normalized_text"])

    # Combine Text + Metadata Features
    X_train_meta = train_df[metadata_cols].values
    X_test_meta = test_df[metadata_cols].values

    X_train = hstack([X_train_text, X_train_meta])
    X_test = hstack([X_test_text, X_test_meta])

    y_train = train_df["label"]
    y_test = test_df["label"]

    # Train Model
    model = LogisticRegression(random_state=42, max_iter=1000)
    model.fit(X_train, y_train)

    # Save Fitted Artifacts
    os.makedirs(models_dir, exist_ok=True)
    joblib.dump(vectorizer, os.path.join(models_dir, "tfidf_vectorizer.joblib"))
    joblib.dump(model, os.path.join(models_dir, "logistic_model.joblib"))
    print(f"\nSaved vectorizer and model artifacts to '{models_dir}/'")

    # Evaluation
    y_pred = model.predict(X_test)

    print("\n==================================================")
    print("      TASK 5: ML PIPELINE EVALUATION (SMOKE TEST) ")
    print("==================================================")
    print("NOTE: Evaluated on 30 synthetic rows. Results serve")
    print("as pipeline validation, NOT real-world accuracy claims.")
    print("--------------------------------------------------")

    print("\n--- CLASSIFICATION REPORT ---")
    print(classification_report(y_test, y_pred, zero_division=0))

    print("--- CONFUSION MATRIX ---")
    labels = sorted(df["label"].unique())
    cm = confusion_matrix(y_test, y_pred, labels=labels)
    cm_df = pd.DataFrame(cm, index=[f"True {l}" for l in labels], columns=[f"Pred {l}" for l in labels])
    print(cm_df)

    print("\n--- PER-LANGUAGE PERFORMANCE BREAKDOWN ---")
    test_df_copy = test_df.copy()
    test_df_copy["predicted_label"] = y_pred

    for lang in ["ENGLISH", "AMHARIC", "MIXED"]:
        lang_sub = test_df_copy[test_df_copy["language"] == lang]
        if len(lang_sub) > 0:
            correct = (lang_sub["label"] == lang_sub["predicted_label"]).sum()
            total = len(lang_sub)
            print(f"Language: {lang:<8} | Correct: {correct}/{total} ({(correct/total)*100:.1f}%)")


if __name__ == "__main__":
    train_and_evaluate()