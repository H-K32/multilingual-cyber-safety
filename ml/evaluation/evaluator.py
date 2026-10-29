# ml/evaluation/evaluator.py
"""
Evaluation utilities and group-aware cross-validation harness for Dagu ML models.

Guarantees:
- Strict group separation (template_group isolation prevents test leakage).
- Calculation of overall, per-class, and per-language metrics.
- Multi-class confusion matrix generation.
- Clear distinction between heuristic threat scores and statistical probabilities.
"""

import os
from pathlib import Path
import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    confusion_matrix,
    f1_score,
    precision_recall_fscore_support,
)
from sklearn.model_selection import StratifiedGroupKFold
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.calibration import CalibratedClassifierCV


LABELS = ["BENIGN", "PHISHING", "SCAM"]
LANGUAGES = ["ENGLISH", "AMHARIC", "MIXED"]


def _summarize_metrics(y_true, y_pred) -> dict:
    precision, recall, weighted_f1, _ = precision_recall_fscore_support(
        y_true, y_pred, average="weighted", zero_division=0
    )
    return {
        "accuracy": accuracy_score(y_true, y_pred),
        "weighted_precision": precision,
        "weighted_recall": recall,
        "weighted_f1": weighted_f1,
        "macro_f1": f1_score(y_true, y_pred, average="macro", zero_division=0),
    }


def evaluate_predictions(
    df: pd.DataFrame,
    y_true: list,
    y_pred: list,
    labels: list[str],
    languages: list[str],
) -> dict:
    """Calculate overall, per-class, and per-language out-of-fold metrics."""
    y_true = list(y_true)
    y_pred = list(y_pred)
    if len(df) != len(y_true) or len(y_true) != len(y_pred):
        raise ValueError("Rows, true labels, and predictions must have equal lengths.")

    class_precision, class_recall, class_f1, class_support = (
        precision_recall_fscore_support(
            y_true,
            y_pred,
            labels=labels,
            average=None,
            zero_division=0,
        )
    )
    per_class = {
        label: {
            "precision": class_precision[index],
            "recall": class_recall[index],
            "f1": class_f1[index],
            "support": int(class_support[index]),
        }
        for index, label in enumerate(labels)
    }

    per_language = {}
    for language in languages:
        mask = df["language"].eq(language)
        if not mask.any():
            per_language[language] = {"count": 0, "metrics": None}
            continue
        language_true = [value for value, include in zip(y_true, mask) if include]
        language_pred = [value for value, include in zip(y_pred, mask) if include]
        per_language[language] = {
            "count": int(mask.sum()),
            "metrics": _summarize_metrics(language_true, language_pred),
        }

    return {
        "overall": _summarize_metrics(y_true, y_pred),
        "per_class": per_class,
        "per_language": per_language,
    }


def get_error_cases(
    df: pd.DataFrame,
    y_true: list,
    y_pred: list,
) -> pd.DataFrame:
    """Return out-of-fold errors with row, language, and template metadata."""
    errors = df.copy()
    errors["true_label"] = list(y_true)
    errors["predicted_label"] = list(y_pred)
    errors = errors[errors["true_label"] != errors["predicted_label"]]
    cols = [c for c in ["id", "true_label", "predicted_label", "language", "template_group", "text"] if c in errors.columns]
    return errors[cols]


def run_group_cv_evaluation(csv_path: str = "dataset/raw/messages.csv") -> dict:
    """Run 5-Fold Stratified Group Cross-Validation on the dataset.

    Verifies group isolation (preventing template leakage), evaluates candidate
    classifiers, and produces confusion matrices and per-class / per-language metrics.
    """
    from ml.preprocessing.text_cleaner import preprocess_message
    from ml.training.train_models import build_feature_pipeline

    all_rows = pd.read_csv(csv_path)
    review_mask = all_rows["annotation_status"].eq("NEEDS_REVIEW")
    eligible_mask = ~review_mask & all_rows["label"].isin(LABELS)
    df = all_rows.loc[eligible_mask].copy().reset_index(drop=True)
    if df.empty:
        raise ValueError("No eligible labeled rows found in dataset.")

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

    models = {
        "Logistic_Regression": LogisticRegression(class_weight="balanced", random_state=42),
        "Linear_SVM": LinearSVC(class_weight="balanced", random_state=42),
        "Calibrated_Linear_SVM": CalibratedClassifierCV(
            LinearSVC(class_weight="balanced", random_state=42), cv=3
        ),
    }

    splitter = StratifiedGroupKFold(n_splits=5, shuffle=True, random_state=42)
    folds = list(
        splitter.split(df["cleaned_text"], df["label"], groups=df["cv_group"])
    )

    # 1. Strict leakage verification: ensure no template group crosses fold boundary
    for fold_idx, (train_idx, val_idx) in enumerate(folds):
        train_groups = set(df["cv_group"].iloc[train_idx])
        val_groups = set(df["cv_group"].iloc[val_idx])
        overlap = train_groups & val_groups
        if overlap:
            raise RuntimeError(
                f"Data leakage detected in fold {fold_idx}: {overlap} crossed boundary!"
            )

    results = {}
    for name, classifier in models.items():
        oof_predictions = [None] * len(df)
        for train_idx, val_idx in folds:
            pipeline = build_feature_pipeline(classifier)
            pipeline.fit(
                df["cleaned_text"].iloc[train_idx],
                df["label"].iloc[train_idx],
            )
            preds = pipeline.predict(df["cleaned_text"].iloc[val_idx])
            for idx, pred in zip(val_idx, preds):
                oof_predictions[idx] = pred

        y_true = df["label"].tolist()
        metrics = evaluate_predictions(df, y_true, oof_predictions, LABELS, LANGUAGES)
        matrix = confusion_matrix(y_true, oof_predictions, labels=LABELS)
        errors = get_error_cases(df, y_true, oof_predictions)

        results[name] = {
            "metrics": metrics,
            "confusion_matrix": matrix.tolist(),
            "confusion_labels": LABELS,
            "error_count": len(errors),
            "errors": errors,
        }

    return {
        "dataset_summary": {
            "total_rows": len(all_rows),
            "excluded_needs_review": int(review_mask.sum()),
            "evaluation_rows": len(df),
            "label_counts": df["label"].value_counts().to_dict(),
            "language_counts": df["language"].value_counts().to_dict(),
            "effective_groups": int(df["cv_group"].nunique()),
        },
        "models": results,
    }


if __name__ == "__main__":
    import sys
    csv = sys.argv[1] if len(sys.argv) > 1 else "dataset/raw/messages.csv"
    res = run_group_cv_evaluation(csv)
    print("=== DAGU ML EVALUATION REPORT ===")
    print(f"Total Rows: {res['dataset_summary']['total_rows']} (Eval: {res['dataset_summary']['evaluation_rows']})")
    print("Label Counts:", res['dataset_summary']['label_counts'])
    print("Language Counts:", res['dataset_summary']['language_counts'])
    print(f"Effective Template Groups: {res['dataset_summary']['effective_groups']}")

    for name, data in res["models"].items():
        print(f"\n--- {name} ---")
        overall = data["metrics"]["overall"]
        print(f"Accuracy: {overall['accuracy']:.4f} | Macro-F1: {overall['macro_f1']:.4f} | Weighted-F1: {overall['weighted_f1']:.4f}")
        print("Per-class F1:", {k: round(v["f1"], 4) for k, v in data["metrics"]["per_class"].items()})
        print("Per-language Macro-F1:", {k: round(v["metrics"]["macro_f1"], 4) for k, v in data["metrics"]["per_language"].items() if v["metrics"]})
        print("Confusion Matrix (rows=true, cols=pred; labels=['BENIGN', 'PHISHING', 'SCAM']):")
        print(data["confusion_matrix"])
        print(f"Total Errors: {data['error_count']}")
