# backend/app/analyzer.py

import os
import joblib

from ml.preprocessing.text_cleaner import preprocess_message
from ml.preprocessing.language_detector import UnicodeLanguageDetector
from detection.rules.security_rules import detect_indicators
from detection.url_analysis.url_analyzer import analyze_urls
from detection.risk_engine.risk_engine import (
    calculate_risk,
    classify_risk,
    determine_threat_type,
)

MODEL_PATH = "ml/models/baseline_model.joblib"

# Instantiate robust language detector
language_detector = UnicodeLanguageDetector()

# Lazy-load trained ML Pipeline
ml_pipeline = None
if os.path.exists(MODEL_PATH):
    try:
        ml_pipeline = joblib.load(MODEL_PATH)
    except Exception as e:
        print(f"[!] Warning: Could not load ML model from {MODEL_PATH}: {e}")


def generate_recommendation(
    classification: str,
    threat_type: str,
) -> str:
    if classification == "HIGH_RISK":
        return (
            "Do not click links or provide credentials, "
            "financial information, OTPs, or passwords. "
            "Verify the message through an official channel."
        )

    if classification == "SUSPICIOUS":
        return (
            "Be cautious. Verify the sender and destination "
            "before clicking links or sharing information."
        )

    return (
        "No major risk indicators were detected. "
        "Continue using normal security precautions."
    )


def analyze_message(message: str) -> dict:
    # 1. Advanced Language & Code-Switch Detection
    lang_info = language_detector.detect_language(message)
    language = lang_info["detected_language"]
    code_switched = lang_info["is_code_switched"]

    # 2. Text Preprocessing & ML Model Inference
    prep_data = preprocess_message(message)
    cleaned_text = prep_data["cleaned_text"]

    ml_pred = None
    if ml_pipeline is not None and cleaned_text.strip():
        try:
            ml_pred = ml_pipeline.predict([cleaned_text])[0]
        except Exception:
            ml_pred = None

    # 3. Rule-Based Security & URL Analysis (Person 1's Modules)
    security_indicators = detect_indicators(message)
    urls, url_indicators = analyze_urls(message)

    # Preserve unique indicator list ordering
    indicators = list(
        dict.fromkeys(security_indicators + url_indicators)
    )

    # 4. Risk Engine Scoring
    risk_score = calculate_risk(indicators)
    classification = classify_risk(risk_score)

    # 5. ML Override Logic: Escalate SAFE to SUSPICIOUS if ML detects malicious text
    if ml_pred in ["PHISHING", "SCAM"] and classification == "SAFE":
        classification = "SUSPICIOUS"

    threat_type = determine_threat_type(indicators)

    recommendation = generate_recommendation(
        classification,
        threat_type,
    )

    return {
        "classification": classification,
        "risk_score": risk_score,
        "threat_type": threat_type,
        "language": language,
        "code_switched": code_switched,
        "indicators": indicators,
        "urls": urls,
        "recommendation": recommendation,
    }