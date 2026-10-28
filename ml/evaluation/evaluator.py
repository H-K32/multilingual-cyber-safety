# ml/evaluation/evaluator.py

import pandas as pd
from sklearn.metrics import (
    accuracy_score,
    f1_score,
    precision_recall_fscore_support,
)


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
    return errors[
        ["id", "true_label", "predicted_label", "language", "template_group", "text"]
    ]