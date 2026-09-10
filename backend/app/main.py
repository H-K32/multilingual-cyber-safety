# backend/app/main.py

from fastapi import FastAPI, HTTPException

from backend.app.analyzer import analyze_message
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse


app = FastAPI(
    title="Multilingual Cyber-Safety Assistant",
    description=(
        "AI-powered cybersecurity analysis for "
        "multilingual digital communications."
    ),
    version="0.3.0",
)


@app.get("/")
def root():
    return {
        "name": "Multilingual Cyber-Safety Assistant",
        "status": "running",
        "version": "0.3.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    if not request.message or not request.message.strip():
        raise HTTPException(status_code=400, detail="Message string cannot be empty.")
        
    return analyze_message(request.message)