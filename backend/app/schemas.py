from typing import Literal

from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    message: str = Field(
        ...,
        json_schema_extra={
            "example": "የእርስዎ telebirr ሂሳብ ታግዷል። http://cbe-verify.top/login"
        },
    )
    message_source: Literal[
        "SMS", "WhatsApp", "Telegram", "Email", "Phone call", "Other", "Unknown"
    ] | None = None
    sender_phone: str | None = Field(default=None, max_length=64)
    sender_identifier: str | None = Field(default=None, max_length=254)
    # The organisation or shortcode the message claims to represent (e.g. "994",
    # "telebirr", "CBE").  Used for sender-identity mismatch detection.
    claimed_sender: str | None = Field(default=None, max_length=64)
    input_method: Literal["text", "image_ocr"] = "text"


class TriggeredRuleItem(BaseModel):
    indicator: str
    category: str
    points: int
    description: str


class MLContribution(BaseModel):
    prediction: str | None = None
    confidence: float = 0.0
    points: int = 0
    is_active: bool = False
    escalated_risk: bool = False


class RiskBreakdown(BaseModel):
    final_risk_score: int
    classification: str
    rule_score: int
    url_score: int
    ml_score: int
    triggered_rules: list[TriggeredRuleItem] = Field(default_factory=list)
    url_indicators: list[TriggeredRuleItem] = Field(default_factory=list)
    urls_detected: list[str] = Field(default_factory=list)
    ml_contribution: MLContribution = Field(default_factory=MLContribution)
    overrides_applied: list[str] = Field(default_factory=list)
    is_statistically_calibrated: bool = False
    calibration_notice: str = ""


class AnalyzeResponse(BaseModel):
    classification: str
    risk_score: int
    threat_type: str
    language: str
    code_switched: bool
    confidence: float = Field(default=0.0, ge=0.0, le=1.0)
    indicators: list[str] = Field(default_factory=list)
    urls: list[str] = Field(default_factory=list)
    recommendation: str
    explanation: str = ""
    message_source: str | None = None
    sender_identifier: str | None = None
    input_method: str = "text"
    analysis_method: str
    phone_reputation: dict | None = None
    # Reputation lookups for phone numbers found inside the message body
    numbers_in_message: list[dict] = Field(default_factory=list)
    # Result of sender-identity verification against known official shortcodes
    sender_verification: dict | None = None
    explanations: dict[str, str] = Field(default_factory=dict)
    risk_breakdown: RiskBreakdown | None = None
