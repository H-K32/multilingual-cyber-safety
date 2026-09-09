from pydantic import BaseModel


class AnalyzeRequest(BaseModel):
    message: str


class AnalyzeResponse(BaseModel):
    classification: str
    risk_score: int
    threat_type: str
    language: str
    code_switched: bool
    indicators: list[str]
    urls: list[str]
    recommendation: str