from pydantic import BaseModel, Field


class AnalyzeRequest(BaseModel):
    message: str = Field(..., example="የእርስዎ telebirr ሂሳብ ታግዷል። http://cbe-verify.top/login")


class AnalyzeResponse(BaseModel):
    classification: str
    risk_score: int
    threat_type: str
    language: str
    code_switched: bool
    indicators: list[str]
    urls: list[str]
    recommendation: str