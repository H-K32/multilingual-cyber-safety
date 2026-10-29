# backend/app/analyzer.py

import os
from pathlib import Path

import joblib
import numpy as np

from ml.preprocessing.text_cleaner import preprocess_message
from ml.preprocessing.language_detector import UnicodeLanguageDetector
from detection.rules.security_rules import detect_indicators
from detection.url_analysis.url_analyzer import analyze_urls
from detection.risk_engine.risk_engine import (
    calculate_risk,
    classify_risk,
    determine_threat_type,
    calculate_detailed_risk_breakdown,
    THREAT_DESCRIPTIONS,
)
from backend.app.phone_reputation import (
    lookup_phone_number,
    extract_phone_numbers_from_text,
    verify_sender_identity,
)

REPO_ROOT = Path(__file__).resolve().parents[2]
MODEL_CANDIDATES = [
    REPO_ROOT / "ml" / "models" / "baseline_model.joblib",
    REPO_ROOT / "models" / "baseline_model.joblib",
    REPO_ROOT / "models" / "logistic_model.joblib",
]


def resolve_model_path() -> str:
    for candidate in MODEL_CANDIDATES:
        if candidate.exists():
            return str(candidate)
    return str(MODEL_CANDIDATES[0])


MODEL_PATH = resolve_model_path()

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


def analyze_message(
    message: str,
    *,
    message_source: str | None = None,
    sender_phone: str | None = None,
    sender_identifier: str | None = None,
    claimed_sender: str | None = None,
    input_method: str = "text",
) -> dict:
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
            elif hasattr(ml_pipeline, "decision_function"):
                scores = ml_pipeline.decision_function([cleaned_text])[0]
                exp_scores = np.exp(scores - np.max(scores))
                probs = exp_scores / np.sum(exp_scores)
                ml_prob = float(max(probs))
        except Exception:
            ml_pred = None
            ml_prob = 0.0

    # 3. Rule-Based Security & URL Analysis
    security_indicators = detect_indicators(message)
    urls, url_indicators = analyze_urls(message)

    # Sender identity verification against known official senders
    sender_verification = verify_sender_identity(sender_phone, claimed_sender)
    sender_mismatch = bool(sender_verification.get("risk_indicator"))

    # Preserve unique indicator list ordering
    all_indicators = security_indicators + url_indicators
    if sender_mismatch:
        all_indicators.append("sender_identity_mismatch")
    indicators = list(dict.fromkeys(all_indicators))

    # 4. Transparent Composite Risk Engine Scoring & Breakdown
    breakdown = calculate_detailed_risk_breakdown(
        security_indicators=security_indicators,
        url_indicators=url_indicators,
        ml_pred=ml_pred,
        ml_prob=ml_prob,
        sender_mismatch=sender_mismatch,
        urls=urls,
    )
    risk_score = breakdown["final_risk_score"]
    classification = breakdown["classification"]

    # 5. Phone reputation lookups
    try:
        phone_reputation = lookup_phone_number(sender_phone)
    except RuntimeError:
        phone_reputation = {
            "status": "service_unavailable",
            "explanation": "The phone reputation database is temporarily unavailable.",
        }

    # Reputation lookups for phone numbers found inside the message body
    extracted_numbers = extract_phone_numbers_from_text(message)
    numbers_in_message = []
    for num in extracted_numbers:
        try:
            lookup = lookup_phone_number(num)
        except RuntimeError:
            lookup = {
                "status": "service_unavailable",
                "explanation": "The phone reputation database is temporarily unavailable.",
            }
        numbers_in_message.append({"phone_number": num, **lookup})

    threat_type = determine_threat_type(indicators, message)
    recommendation = generate_recommendation(classification, threat_type)
    explanation = THREAT_DESCRIPTIONS.get(
        threat_type,
        THREAT_DESCRIPTIONS.get("BENIGN", {"explanation": "No suspicious indicators were identified."}),
    )["explanation"]
    confidence = round(float(ml_prob), 4) if ml_pred is not None else 0.0

    text_explanation = (
        "Message wording indicators: " + ", ".join(security_indicators) + "."
        if security_indicators
        else "No message-wording indicators were detected by the configured rules."
    )
    url_explanation = (
        "URL indicators: " + ", ".join(url_indicators) + "."
        if url_indicators
        else (
            "No URLs were present."
            if not urls
            else "URLs were present, but the configured URL rules found no indicators."
        )
    )
    sender_verification_explanation = sender_verification.get("explanation", "")
    limitations = (
        "The analysis uses deterministic message and URL rules"
        + (
            " and the loaded ML model for this message."
            if ml_pred is not None
            else "; no ML prediction was used for this message."
        )
        + " Results are heuristic threat indicators, not proof of malicious intent. "
        + "The risk score is a deterministic composite index, not a statistically calibrated probability. "
        + (
            "No matching phone reports do not establish that a number is safe."
            if phone_reputation["status"] == "no_reports_found"
            else ""
        )
        + (
            " Screenshot OCR uses bilingual Amharic and English recognition; review "
            "the editable text for recognition errors."
            if input_method == "image_ocr"
            else ""
        )
    )

    return {
        "classification": classification,
        "risk_score": risk_score,
        "threat_type": threat_type,
        "language": language,
        "code_switched": code_switched,
        "confidence": confidence,
        "indicators": indicators,
        "urls": urls,
        "recommendation": recommendation,
        "explanation": explanation,
        "message_source": message_source,
        "sender_identifier": sender_identifier,
        "input_method": input_method,
        "analysis_method": (
            "rules_urls_and_ml" if ml_pred is not None else "rules_and_urls"
        ),
        "phone_reputation": phone_reputation,
        "numbers_in_message": numbers_in_message,
        "sender_verification": sender_verification,
        "risk_breakdown": breakdown,
        "explanations": {
            "message": text_explanation,
            "urls": url_explanation,
            "sender_number": phone_reputation["explanation"],
            "sender_verification": sender_verification_explanation,
            "context": (
                "The selected message source is context only and does not affect "
                "the risk score."
                if message_source
                else "No message source was provided."
            ),
            "ocr": (
                "Text was extracted from an image using bilingual Amharic and English OCR; "
                "review the editable text for recognition errors."
                if input_method == "image_ocr"
                else ""
            ),
            "limitations": limitations,
        },
    }
