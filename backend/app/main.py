# backend/app/main.py

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware

from backend.app.analyzer import analyze_message
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse

app = FastAPI(
    title="Multilingual Cyber-Safety Assistant",
    description=(
        "AI-powered cybersecurity analysis for "
        "multilingual digital communications."
    ),
    version="0.4.0",
)

# Enable CORS for mobile & web clients
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/")
def root():
    return {
        "name": "Multilingual Cyber-Safety Assistant",
        "status": "running",
        "version": "0.4.0",
    }


@app.post("/analyze", response_model=AnalyzeResponse)
def analyze(request: AnalyzeRequest):
    # Reject empty or whitespace-only messages
    if not request.message or not request.message.strip():
        raise HTTPException(
            status_code=400,
            detail="Message payload cannot be empty or whitespace only.",
        )

    # Reject oversized payloads
    if len(request.message) > 5000:
        raise HTTPException(
            status_code=400,
            detail="Message exceeds maximum allowed length of 5000 characters.",
        )

    return analyze_message(request.message)