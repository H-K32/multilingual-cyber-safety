# ml/training/train_models.py

import os
from pathlib import Path

import joblib
import pandas as pd
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV
from sklearn.metrics import confusion_matrix

from ml.preprocessing.text_cleaner import preprocess_message
from ml.evaluation.evaluator import evaluate_predictions, get_error_cases

MODEL_SAVE_PATH = Path(__file__).resolve().parents[1] / "models" / "baseline_model.joblib"
LABELS = ["BENIGN", "PHISHING", "SCAM"]
LANGUAGES = ["ENGLISH", "AMHARIC", "MIXED"]

def build_feature_pipeline(classifier):
    """Combines Word + Character N-Grams with a classifier."""
    vectorizer = FeatureUnion([
        ('word_tfidf', TfidfVectorizer(ngram_range=(1, 2), analyzer='word')),
        ('char_tfidf', TfidfVectorizer(ngram_range=(3, 5), analyzer='char'))
    ])
    return Pipeline([
        ('features', vectorizer),
        ('clf', classifier)
    ])

def train_and_save_pipeline(csv_path: str):
    all_rows = pd.read_csv(csv_path)
    review_mask = all_rows["annotation_status"].eq("NEEDS_REVIEW")
    eligible_mask = ~review_mask & all_rows["label"].isin(LABELS)
    df = all_rows.loc[eligible_mask].copy().reset_index(drop=True)
    if df.empty:
        raise ValueError("No eligible labeled rows remain after filtering the dataset.")

    df["cleaned_text"] = [
        preprocess_message(text)["cleaned_text"] for text in df["text"]
    ]

    named_groups = df["template_group"].fillna("").astype(str).str.strip()
    singleton_prefix = "__ungrouped_row__"
    while any(group.startswith(singleton_prefix) for group in named_groups if group):
        singleton_prefix += "_"
    df["cv_group"] = [
        group if group else f"{singleton_prefix}{row_id}"
        for group, row_id in zip(named_groups, df["id"])
    ]
    named_group_count = int(named_groups[named_groups.ne("")].nunique())
    ungrouped_count = int(named_groups.eq("").sum())

    models = {
        "Logistic_Regression": LogisticRegression(class_weight='balanced', random_state=42),
        "Linear_SVM": LinearSVC(class_weight='balanced', random_state=42),
        "Calibrated_Linear_SVM": CalibratedClassifierCV(LinearSVC(class_weight='balanced', random_state=42), cv=3),
    }

    print("=== DATASET ===")
    print(f"Total rows: {len(all_rows)}")
    print(f"Excluded NEEDS_REVIEW rows: {int(review_mask.sum())}")
    print(f"Training rows: {len(df)}")
    for label in LABELS:
        print(f"{label} count: {int(df['label'].eq(label).sum())}")
    for language in LANGUAGES:
        print(f"{language} count: {int(df['language'].eq(language).sum())}")
    print(
        "Template groups: {} effective ({} named, {} blank treated as singleton groups)".format(
            df["cv_group"].nunique(), named_group_count, ungrouped_count
        )
    )

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(
        splitter.split(df["cleaned_text"], df["label"], groups=df["cv_group"])
    )
    for train_indices, validation_indices in folds:
        train_groups = set(df["cv_group"].iloc[train_indices])
        validation_groups = set(df["cv_group"].iloc[validation_indices])
        if train_groups & validation_groups:
            raise RuntimeError("A template group crossed a CV train/validation boundary.")

    results = {}
    print("\n=== GROUP-AWARE CV RESULTS ===")
    for name, classifier in models.items():
        oof_predictions = [None] * len(df)
        for train_indices, validation_indices in folds:
            pipeline = build_feature_pipeline(classifier)
            pipeline.fit(
                df["cleaned_text"].iloc[train_indices],
                df["label"].iloc[train_indices],
            )
            predictions = pipeline.predict(df["cleaned_text"].iloc[validation_indices])
            for index, prediction in zip(validation_indices, predictions):
                oof_predictions[index] = prediction

        if any(prediction is None for prediction in oof_predictions):
            raise RuntimeError(f"Incomplete out-of-fold predictions for {name}.")

        y_true = df["label"].tolist()
        metrics = evaluate_predictions(df, y_true, oof_predictions, LABELS, LANGUAGES)
        errors = get_error_cases(df, y_true, oof_predictions)
        results[name] = {"metrics": metrics, "errors": errors}

        print(f"\n{name.replace('_', ' ')}")
        print("Overall:")
        for metric, value in metrics["overall"].items():
            print(f"  {metric}: {value:.4f}")
        print("Per class:")
        for label, values in metrics["per_class"].items():
            print(
                "  {}: precision={:.4f} recall={:.4f} f1={:.4f} support={}".format(
                    label, values["precision"], values["recall"], values["f1"], values["support"]
                )
            )
        print("Per language:")
        for language, values in metrics["per_language"].items():
            if values["metrics"] is None:
                print(f"  {language}: no samples")
                continue
            language_metrics = values["metrics"]
            print(
                "  {} (n={}): accuracy={:.4f} weighted_precision={:.4f} "
                "weighted_recall={:.4f} weighted_f1={:.4f} macro_f1={:.4f}".format(
                    language,
                    values["count"],
                    language_metrics["accuracy"],
                    language_metrics["weighted_precision"],
                    language_metrics["weighted_recall"],
                    language_metrics["weighted_f1"],
                    language_metrics["macro_f1"],
                )
            )

        matrix = confusion_matrix(y_true, oof_predictions, labels=LABELS)
        print("Confusion matrix (rows=true, columns=predicted; labels={}):".format(LABELS))
        print(matrix)
        print(f"Total errors: {len(errors)}")
        if errors.empty:
            print("Error rows: none")
        else:
            print(
                errors[["id", "true_label", "predicted_label", "language", "template_group"]]
                .to_string(index=False)
            )

    def comparison_key(name):
        metrics = results[name]["metrics"]
        class_f1 = [values["f1"] for values in metrics["per_class"].values()]
        language_f1 = [
            values["metrics"]["macro_f1"]
            for values in metrics["per_language"].values()
            if values["metrics"] is not None
        ]
        return (
            metrics["overall"]["macro_f1"],
            metrics["overall"]["weighted_f1"],
            min(class_f1),
            sum(language_f1) / len(language_f1) if language_f1 else 0.0,
            metrics["overall"]["accuracy"],
        )

    selected_model = max(models, key=comparison_key)
    print("\n=== MODEL COMPARISON ===")
    for name in models:
        metrics = results[name]["metrics"]
        class_f1 = " ".join(
            f"{label}={values['f1']:.4f}"
            for label, values in metrics["per_class"].items()
        )
        language_f1 = " ".join(
            f"{language}={values['metrics']['macro_f1']:.4f}"
            for language, values in metrics["per_language"].items()
            if values["metrics"] is not None
        )
        print(
            "{}: macro_f1={:.4f}, weighted_f1={:.4f}, per_class_f1=[{}], "
            "per_language_macro_f1=[{}]".format(
                name.replace("_", " "),
                metrics["overall"]["macro_f1"],
                metrics["overall"]["weighted_f1"],
                class_f1,
                language_f1,
            )
        )

    print(f"\n=== SELECTED MODEL ===\n{selected_model.replace('_', ' ')}")
    print("Selection order: macro F1, weighted F1, worst per-class F1, mean per-language macro F1, accuracy.")

    print("\nRetraining selected model on all eligible rows...")
    MODEL_SAVE_PATH.parent.mkdir(parents=True, exist_ok=True)
    final_pipeline = build_feature_pipeline(models[selected_model])
    final_pipeline.fit(df["cleaned_text"], df["label"])
    joblib.dump(final_pipeline, MODEL_SAVE_PATH)

    print("\n=== SAVED MODEL ===")
    print(f"Path: {MODEL_SAVE_PATH.resolve()}")
    print(f"Type: {type(final_pipeline).__module__}.{type(final_pipeline).__name__}")
    print(f"Bytes: {MODEL_SAVE_PATH.stat().st_size}")

    print("\n=== LOAD TEST ===")
    try:
        loaded_pipeline = joblib.load(MODEL_SAVE_PATH)
        if not isinstance(loaded_pipeline, Pipeline):
            raise TypeError("Saved object is not an sklearn Pipeline.")
        sample_prediction = loaded_pipeline.predict([df["cleaned_text"].iloc[0]])[0]
        if sample_prediction not in LABELS:
            raise ValueError(f"Unexpected prediction label: {sample_prediction}")
        print(f"PASS: loaded complete Pipeline; sample prediction={sample_prediction}")
    except Exception as error:
        print(f"FAIL: {type(error).__name__}: {error}")
        raise

if __name__ == "__main__":
    csv_file = "dataset/raw/messages.csv"
    if os.path.exists(csv_file):
        train_and_save_pipeline(csv_file)
    else:
        print(f"Error: {csv_file} not found.")
