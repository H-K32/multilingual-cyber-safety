from fastapi import FastAPI

from backend.app.analyzer import analyze_message
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse


app = FastAPI(
    title="Multilingual Cyber-Safety Assistant",
    description=(
        "AI-powered cybersecurity analysis for "
        "multilingual digital communications."
    ),
    version="0.1.0",
)


@app.get("/")
def root():
    return {
        "name": "Multilingual Cyber-Safety Assistant",
        "status": "running",
        "version": "0.1.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    return analyze_message(request.message)