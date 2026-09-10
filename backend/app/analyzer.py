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
    THREAT_DESCRIPTIONS,
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
    # Use threat-specific recommendation if available
    if threat_type in THREAT_DESCRIPTIONS:
        return THREAT_DESCRIPTIONS[threat_type]["recommendation"]

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
    ml_prob = 0.0
    if ml_pipeline is not None and cleaned_text.strip():
        try:
            ml_pred = ml_pipeline.predict([cleaned_text])[0]
            if hasattr(ml_pipeline, "predict_proba"):
                probs = ml_pipeline.predict_proba([cleaned_text])[0]
                ml_prob = float(max(probs))
        except Exception:
            ml_pred = None
            ml_prob = 0.0

    # 3. Rule-Based Security & URL Analysis
    security_indicators = detect_indicators(message)
    urls, url_indicators = analyze_urls(message)

    # Preserve unique indicator list ordering
    indicators = list(
        dict.fromkeys(security_indicators + url_indicators)
    )

    # 4. Composite Risk Engine Scoring
    rule_score = calculate_risk(indicators)
    ml_score = int(ml_prob * 40) if ml_pred in ["PHISHING", "SCAM", 1] else 0
    
    # Combined composite score bounded to 100
    risk_score = min(rule_score + ml_score, 100)

    # High-severity override for direct credential harvesting vectors
    if ("credential_request" in indicators or "otp_request" in indicators) and ("lookalike_domain" in indicators or "ip_address_url" in indicators):
        risk_score = max(risk_score, 85)

    classification = classify_risk(risk_score)

    # 5. ML Escalation: Escalate SAFE to SUSPICIOUS if ML detects threat intent
    if ml_pred in ["PHISHING", "SCAM"] and classification == "SAFE":
        classification = "SUSPICIOUS"
        risk_score = max(risk_score, 45)

    threat_type = determine_threat_type(indicators, message)

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