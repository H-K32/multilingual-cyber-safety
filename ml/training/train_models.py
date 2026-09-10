# ml/training/train_models.py

import os
import joblib
import pandas as pd
import numpy as np
from sklearn.model_selection import StratifiedKFold
from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.pipeline import FeatureUnion, Pipeline
from sklearn.linear_model import LogisticRegression
from sklearn.svm import LinearSVC
from sklearn.metrics import confusion_matrix

from ml.preprocessing.text_cleaner import preprocess_message
from ml.evaluation.evaluator import evaluate_by_language, get_error_cases

MODEL_SAVE_PATH = "ml/models/baseline_model.joblib"

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
    df = pd.read_csv(csv_path)
    df['cleaned_text'] = [preprocess_message(t)['cleaned_text'] for t in df['text']]
    
    models = {
        "Logistic_Regression": LogisticRegression(class_weight='balanced', random_state=42),
        "Linear_SVM": LinearSVC(class_weight='balanced', random_state=42)
    }
    
    print("=" * 60)
    print("DAY 2: MULTILINGUAL MODEL TRAINING, EVALUATION & SERIALIZATION")
    print("=" * 60)
    
    skf = StratifiedKFold(n_splits=5, shuffle=True, random_state=42)
    best_f1 = -1.0
    best_model_name = ""
    
    for name, clf in models.items():
        print(f"\n---> Evaluating Model: {name}")
        pipeline = build_feature_pipeline(clf)
        
        all_y_true, all_y_pred, test_indices = [], [], []
        
        for train_idx, test_idx in skf.split(df['cleaned_text'], df['label']):
            X_train, X_test = df['cleaned_text'].iloc[train_idx], df['cleaned_text'].iloc[test_idx]
            y_train, y_test = df['label'].iloc[train_idx], df['label'].iloc[test_idx]
            
            pipeline.fit(X_train, y_train)
            preds = pipeline.predict(X_test)
            
            all_y_true.extend(y_test)
            all_y_pred.extend(preds)
            test_indices.extend(test_idx)
            
        df_test_reordered = df.iloc[test_indices].copy()
        
        # Subgroup metrics
        metrics_df = evaluate_by_language(df_test_reordered, all_y_true, all_y_pred)
        print("\nPerformance Metrics:")
        print(metrics_df.to_string(index=False))
        
        # Confusion Matrix
        labels = sorted(list(set(all_y_true)))
        cm = confusion_matrix(all_y_true, all_y_pred, labels=labels)
        print(f"\nConfusion Matrix ({labels}):")
        print(cm)
        
        # Categorized Error Analysis
        errors = get_error_cases(df_test_reordered, all_y_true, all_y_pred)
        print(f"\nTotal Misclassifications: {len(errors)} / {len(df)}")
        if not errors.empty:
            print(errors[['id', 'language', 'label', 'predicted_label']].to_string(index=False))
            
        # Track best performing overall model
        overall_f1 = metrics_df[metrics_df['group'] == 'OVERALL']['f1_score'].values[0]
        if overall_f1 > best_f1:
            best_f1 = overall_f1
            best_model_name = name

    # Train final best model on complete dataset and serialize to disk
    print(f"\n[+] Fitting best performing architecture ({best_model_name}) on full dataset...")
    os.makedirs(os.path.dirname(MODEL_SAVE_PATH), exist_ok=True)
    final_pipeline = build_feature_pipeline(models[best_model_name])
    final_pipeline.fit(df['cleaned_text'], df['label'])
    
    joblib.dump(final_pipeline, MODEL_SAVE_PATH)
    print(f"[✓] Model successfully serialized to: {MODEL_SAVE_PATH}")

if __name__ == "__main__":
    csv_file = "dataset/raw/messages.csv"
    if os.path.exists(csv_file):
        train_and_save_pipeline(csv_file)
    else:
        print(f"Error: {csv_file} not found.")