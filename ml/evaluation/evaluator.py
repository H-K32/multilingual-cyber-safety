# ml/evaluation/evaluator.py

import pandas as pd
from sklearn.metrics import accuracy_score, precision_recall_fscore_support

def evaluate_by_language(df_test: pd.DataFrame, y_true: list, y_pred: list) -> pd.DataFrame:
    """
    Evaluates classification performance across the entire test set
    and breaks down metrics by language sub-groups (ENGLISH, AMHARIC, MIXED).
    """
    df_eval = df_test.copy()
    df_eval['y_true'] = y_true
    df_eval['y_pred'] = y_pred
    
    metrics = []
    
    # 1. Overall Metrics
    acc = accuracy_score(y_true, y_pred)
    p, r, f1, _ = precision_recall_fscore_support(y_true, y_pred, average='weighted', zero_division=0)
    metrics.append({
        "group": "OVERALL",
        "count": len(df_eval),
        "accuracy": round(acc, 3),
        "precision": round(p, 3),
        "recall": round(r, 3),
        "f1_score": round(f1, 3)
    })
    
    # 2. Per-Language Subgroup Metrics
    for lang in ['ENGLISH', 'AMHARIC', 'MIXED']:
        sub = df_eval[df_eval['language'] == lang]
        if len(sub) == 0:
            continue
        sub_acc = accuracy_score(sub['y_true'], sub['y_pred'])
        sub_p, sub_r, sub_f1, _ = precision_recall_fscore_support(
            sub['y_true'], sub['y_pred'], average='weighted', zero_division=0
        )
        metrics.append({
            "group": lang,
            "count": len(sub),
            "accuracy": round(sub_acc, 3),
            "precision": round(sub_p, 3),
            "recall": round(sub_r, 3),
            "f1_score": round(sub_f1, 3)
        })
        
    return pd.DataFrame(metrics)

def get_error_cases(df_test: pd.DataFrame, y_true: list, y_pred: list) -> pd.DataFrame:
    """Extracts misclassified examples for qualitative error analysis."""
    df_eval = df_test.copy()
    df_eval['predicted_label'] = y_pred
    errors = df_eval[df_eval['label'] != df_eval['predicted_label']]
    return errors[['id', 'text', 'language', 'label', 'predicted_label', 'threat_type']]