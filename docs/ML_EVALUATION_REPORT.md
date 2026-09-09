# Multilingual Cyber Safety: Preprocessing, Language Detection & ML Pipeline Report

## Project Overview

This document summarizes the implementations and baseline evaluation for Tasks 3, 4, and 5 of the Multilingual Cyber Safety detection engine (Amharic, English, and Code-Switched messages).

---

## Task 3: Preprocessing & Metadata Extraction Architecture

To retain cybersecurity threat signals while supporting effective NLP vectorization, a **dual-text pipeline** was implemented in `ml/preprocessor.py`:

1. **Original Text**: Preserved verbatim for exact security rule matching, domain/URL inspection, and threat indicator extraction.
2. **Normalized Text**: Standardized for machine learning feature extraction using token replacements:
   - URLs replaced with `<URL>`
   - Currencies (`$`, `ETB`, `Birr`, `ብር`) replaced with `<CURRENCY>`
   - Mentions (`@user`) replaced with `<MENTION>`
   - Numbers replaced with `<NUM>`
3. **Structured Security Metadata Features**:
   - `has_url` & `url_count`
   - `has_currency`
   - `has_mention`
   - `is_shouting` (ALL-CAPS word detection)
   - `suspicious_unicode_count`

Preprocessed output dataset is saved to `dataset/processed/preprocessed_messages.csv`.

---

## Task 4: Script-Based Language & Code-Switching Detection

Implemented in `ml/language_detector.py` using Unicode range inspection:

- **Ethiopic Script Range**: `U+1200`–`U+139F` and `U+2D80`–`U+2DDF`
- **Latin Script Range**: `A-Z`, `a-z`

### Critical Rules

- URLs are stripped **before** script character ratio calculations to avoid misclassifying Amharic texts containing URLs as `MIXED`.
- **Classification Threshold**: Minimum 3 letters required; minor script ratio threshold set to 8% for `MIXED` (code-switched) classification.

### Evaluation Results (Synthetic Benchmark)

- **Language Detection Accuracy**: 30/30 (100.0%)
- **Code-Switching Detection Accuracy**: 30/30 (100.0%)

_Limitation Note_: Detects script, not semantic language. Latin-transliterated Amharic will be recognized as `ENGLISH`.

---

## Task 5: ML Pipeline Baseline (Smoke Test)

Implemented in `ml/train_pipeline.py` using TF-IDF word n-grams (1,2) combined with structured metadata features fed into a `LogisticRegression` classifier.

### Results on 30-Row Synthetic Dataset (24 Train / 6 Test)

- **Macro F1-Score**: 0.60
- **Weighted Accuracy**: 83% (6 test samples)
- **Model Artifacts Saved**: `models/tfidf_vectorizer.joblib`, `models/logistic_model.joblib`

### Disclaimer & Next Steps

This evaluation serves strictly as a **pipeline validation / smoke test**. Accuracy metrics on a 30-row synthetic dataset do not reflect real-world performance.

### Planned System Enhancements:

1. Dataset expansion with real-world Amharic and English scam/phishing texts.
2. Character n-gram tokenization to handle spelling variations and Latin-transliterated Amharic.
3. Integration with cybersecurity rule engine (URL domain reputation, regex indicators).
