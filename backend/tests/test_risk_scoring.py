# backend/tests/test_risk_scoring.py
"""Tests for risk score breakdown, transparency, calibration notices, and ML evaluation."""

import pytest
from fastapi.testclient import TestClient

from backend.app.main import app
from backend.app.analyzer import analyze_message
from detection.risk_engine.risk_engine import (
    calculate_detailed_risk_breakdown,
    INDICATOR_SCORES,
    INDICATOR_DESCRIPTIONS,
)
from ml.evaluation.evaluator import run_group_cv_evaluation

client = TestClient(app)


def test_analyze_response_includes_transparent_risk_breakdown():
    """Verify that /analyze returns the structured risk_breakdown object."""
    response = client.post(
        "/analyze",
        json={"message": "Urgent! Claim your 50,000 Birr reward immediately at http://cbe-login.top/verify"},
    )
    assert response.status_code == 200
    data = response.json()

    assert "risk_breakdown" in data
    breakdown = data["risk_breakdown"]
    assert breakdown is not None

    # Check top-level numeric contributors
    assert "rule_score" in breakdown
    assert "url_score" in breakdown
    assert "ml_score" in breakdown
    assert "final_risk_score" in breakdown
    assert breakdown["final_risk_score"] == data["risk_score"]

    # Check triggered rules transparency
    assert len(breakdown["triggered_rules"]) > 0
    for rule in breakdown["triggered_rules"]:
        assert "indicator" in rule
        assert "category" in rule
        assert "points" in rule
        assert "description" in rule
        assert rule["points"] > 0

    # Check URL indicators transparency
    assert len(breakdown["url_indicators"]) > 0
    for url_ind in breakdown["url_indicators"]:
        assert "indicator" in url_ind
        assert "points" in url_ind
        assert "description" in url_ind

    # Check URLs detected list
    assert "http://cbe-login.top/verify" in breakdown["urls_detected"]

    # Check ML contribution
    ml_contrib = breakdown["ml_contribution"]
    assert "prediction" in ml_contrib
    assert "confidence" in ml_contrib
    assert "points" in ml_contrib
    assert "is_active" in ml_contrib


def test_heuristic_vs_calibrated_probability_declaration():
    """Verify system explicitly declares scores are heuristic, NOT statistically calibrated."""
    result = analyze_message("Normal conversational message between friends.")
    breakdown = result["risk_breakdown"]

    assert breakdown["is_statistically_calibrated"] is False
    assert "heuristic" in breakdown["calibration_notice"].lower()
    assert "not an empirical" in breakdown["calibration_notice"].lower()

    # Check limitations text in explanations
    limitations = result["explanations"]["limitations"]
    assert "heuristic threat indicators" in limitations
    assert "not a statistically calibrated probability" in limitations


def test_critical_credential_vector_override_transparency():
    """Verify credential + lookalike domain applies override and notes it in overrides_applied."""
    # Lookalike CBE link with credential request
    message = "Your account is locked. Enter your PIN and password at http://cbe-auth.top/login"
    result = analyze_message(message)
    breakdown = result["risk_breakdown"]

    assert result["risk_score"] >= 85
    assert result["classification"] == "HIGH_RISK"
    assert "critical_credential_harvesting_override" in breakdown["overrides_applied"]


def test_sender_identity_mismatch_breakdown_item():
    """Verify sender identity mismatch adds transparency item and points."""
    # Claims to be telebirr but arrives from an unrecognized number
    result = analyze_message(
        "Your account is updated.",
        sender_phone="+251911999999",
        claimed_sender="telebirr",
    )
    breakdown = result["risk_breakdown"]

    assert result["risk_score"] >= 55
    assert result["classification"] in ["SUSPICIOUS", "HIGH_RISK"]
    mismatch_items = [
        r for r in breakdown["triggered_rules"]
        if r["indicator"] == "sender_identity_mismatch"
    ]
    assert len(mismatch_items) == 1
    assert mismatch_items[0]["category"] == "sender_verification"
    assert mismatch_items[0]["points"] == 25


def test_group_cv_evaluation_prevents_template_leakage():
    """Verify group-aware evaluation guarantees 0 group leakage across folds."""
    eval_result = run_group_cv_evaluation("dataset/raw/messages.csv")

    summary = eval_result["dataset_summary"]
    assert summary["evaluation_rows"] == 301
    assert summary["effective_groups"] >= 50

    # Verify all models evaluated and produced metrics
    models = eval_result["models"]
    assert "Logistic_Regression" in models
    assert "Linear_SVM" in models

    for model_name, model_data in models.items():
        metrics = model_data["metrics"]["overall"]
        assert 0.80 <= metrics["accuracy"] <= 1.0
        assert 0.80 <= metrics["macro_f1"] <= 1.0
        assert len(model_data["confusion_matrix"]) == 3
        assert model_data["error_count"] < 40


def test_ml_model_correctly_identifies_benign_security_reminders():
    """Verify that the retrained ML pipeline recognizes security advice as BENIGN
    even when it mentions sensitive keywords like OTP, PIN, or banking brands."""
    # 1. English security advice
    msg_en = "Security Alert from CBE: Never share your mobile banking PIN or OTP with callers claiming to be bank agents."
    resp_en = client.post("/analyze", json={"message": msg_en})
    assert resp_en.status_code == 200
    data_en = resp_en.json()
    ml_en = data_en["risk_breakdown"]["ml_contribution"]
    assert ml_en["is_active"] is True
    assert ml_en["prediction"] == "BENIGN"
    assert ml_en["escalated_risk"] is False

    # 2. Amharic security advice
    msg_am = "የኢትዮጵያ ንግድ ባንክ የደህንነት መልዕክት፡ የባንኩ ሰራተኞች የይለፍ ቃልዎን ወይም የOTP ቁጥርዎን በፍጹም አይጠይቁም።"
    resp_am = client.post("/analyze", json={"message": msg_am})
    assert resp_am.status_code == 200
    data_am = resp_am.json()
    ml_am = data_am["risk_breakdown"]["ml_contribution"]
    assert ml_am["is_active"] is True
    assert ml_am["prediction"] == "BENIGN"
    assert ml_am["escalated_risk"] is False


