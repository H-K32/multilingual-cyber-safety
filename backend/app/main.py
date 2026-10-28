# backend/app/main.py

from fastapi import FastAPI, File, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.analyzer import analyze_message
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse
from backend.app.phone_reputation import lookup_phone_number, submit_report, ALLOWED_CATEGORIES, extract_phone_numbers_from_text
from backend.app.image_ocr import (
    ALLOWED_IMAGE_CONTENT_TYPES,
    MAX_IMAGE_BYTES,
    InvalidImageError,
    OCRProcessingError,
    OCREngineUnavailableError,
    extract_text_from_image,
)

app = FastAPI(
    title="Multilingual Cyber-Safety Assistant",
    description=(
        "Explainable rule-based multilingual text and URL analysis, with optional "
        "ML predictions only when a trained model loads and produces a prediction."
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

    return analyze_message(
        request.message,
        message_source=request.message_source,
        sender_phone=request.sender_phone,
        sender_identifier=request.sender_identifier,
        claimed_sender=request.claimed_sender,
        input_method=request.input_method,
    )


@app.post("/analyze/image")
async def analyze_image(file: UploadFile = File(...)):
    try:
        if file.content_type not in ALLOWED_IMAGE_CONTENT_TYPES:
            raise HTTPException(
                status_code=415,
                detail="Only PNG and JPEG images are supported.",
            )

        image_bytes = await file.read(MAX_IMAGE_BYTES + 1)
        if len(image_bytes) > MAX_IMAGE_BYTES:
            raise HTTPException(
                status_code=413,
                detail="The uploaded image exceeds the 5 MB limit.",
            )
        if not image_bytes:
            raise HTTPException(status_code=400, detail="The uploaded image is empty.")

        try:
            extracted_text = extract_text_from_image(image_bytes, file.content_type)
        except InvalidImageError as error:
            raise HTTPException(status_code=400, detail=str(error)) from error
        except OCRProcessingError as error:
            raise HTTPException(status_code=422, detail=str(error)) from error
        except OCREngineUnavailableError as error:
            raise HTTPException(status_code=503, detail=str(error)) from error

        # Extract phone numbers found in the OCR text and look them up
        extracted_phones = extract_phone_numbers_from_text(extracted_text)
        phone_lookups = [
            {"phone_number": num, **lookup_phone_number(num)}
            for num in extracted_phones
        ]

        # Run full message analysis on the extracted text
        analysis = analyze_message(extracted_text, input_method="image_ocr")

        return {
            "extracted_text": extracted_text,
            "ocr_engine": "Tesseract",
            "ocr_languages": ["eng"],
            "numbers_in_image": phone_lookups,
            "analysis": analysis,
        }
    finally:
        await file.close()


@app.post("/check-number")
def check_number(body: dict):
    phone = body.get("phone_number", "") if isinstance(body, dict) else ""
    if not phone or not str(phone).strip():
        raise HTTPException(status_code=400, detail="phone_number is required.")
    return lookup_phone_number(str(phone).strip())


@app.post("/report")
def report_number(body: dict):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")
    phone = str(body.get("phone_number", "")).strip()
    if not phone:
        raise HTTPException(status_code=400, detail="phone_number is required.")
    raw_cats = body.get("categories", [])
    if not isinstance(raw_cats, list) or not raw_cats:
        raise HTTPException(
            status_code=400,
            detail=f"categories must be a non-empty list. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}.",
        )
    evidence = str(body.get("evidence_note", ""))[:500]
    result = submit_report(phone, raw_cats, evidence)
    if result["status"] in {"invalid_number", "invalid_categories"}:
        raise HTTPException(status_code=400, detail=result["explanation"])
    return result