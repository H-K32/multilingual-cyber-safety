# backend/app/main.py

from contextlib import asynccontextmanager
import ipaddress
import os

from fastapi import Depends, FastAPI, File, HTTPException, Query, Request, UploadFile
from fastapi.middleware.cors import CORSMiddleware

from backend.app.analyzer import analyze_message
from backend.app.schemas import AnalyzeRequest, AnalyzeResponse
from backend.app.auth import SecurityAnalyst, require_analyst_role
from backend.app.security_feed import (
    get_security_feed,
    get_security_feed_event,
    update_feed_event_status,
)
from backend.app.phone_reputation import (
    lookup_phone_number,
    submit_report,
    submit_dispute,
    get_disputes,
    update_dispute_status,
    get_reported_numbers,
    ALLOWED_CATEGORIES,
    extract_phone_numbers_from_text,
)
from backend.app.image_ocr import (
    ALLOWED_IMAGE_CONTENT_TYPES,
    MAX_IMAGE_BYTES,
    InvalidImageError,
    OCRProcessingError,
    OCREngineUnavailableError,
    extract_text_from_image,
    determine_ocr_language_config,
)
from backend.app.rate_limiter import report_rate_limiter, dispute_rate_limiter
from backend.app.db import init_db, close_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    init_db()
    yield
    close_db()


app = FastAPI(
    title="Dagu — Multilingual Cyber-Safety Platform",
    description=(
        "“Check Before You Trust.” Explainable multilingual scam detection, "
        "phone reputation lookup, and community threat reporting."
    ),
    version="0.5.0",
    lifespan=lifespan,
)

# Enable CORS for mobile & web clients (configurable via CORS_ALLOWED_ORIGINS)
_cors_origins_raw = os.environ.get("CORS_ALLOWED_ORIGINS", "*").strip()
_cors_origins = (
    [orig.strip() for orig in _cors_origins_raw.split(",") if orig.strip()]
    if _cors_origins_raw != "*"
    else ["*"]
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=_cors_origins,
    allow_credentials=False if _cors_origins == ["*"] else True,
    allow_methods=["*"],
    allow_headers=["*"],
)


def get_client_ip(request: Request) -> str:
    """Extract client IP safely from request, supporting trusted reverse proxies."""
    trust_proxy = os.environ.get("TRUST_PROXY_HEADERS", "true").lower() in ("true", "1", "yes")

    if trust_proxy:
        forwarded = request.headers.get("x-forwarded-for")
        if forwarded:
            parts = [p.strip() for p in forwarded.split(",") if p.strip()]
            for candidate in reversed(parts):
                try:
                    ipaddress.ip_address(candidate)
                    return candidate
                except ValueError:
                    continue
        real_ip = request.headers.get("x-real-ip")
        if real_ip:
            candidate = real_ip.strip()
            try:
                ipaddress.ip_address(candidate)
                return candidate
            except ValueError:
                pass

    if request.client and request.client.host:
        return request.client.host
    return "127.0.0.1"


@app.get("/")
def root():
    return {
        "name": "Dagu — Multilingual Cyber-Safety Platform",
        "motto": "Check Before You Trust.",
        "status": "running",
        "version": "0.5.0",
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
        phone_lookups = []
        for num in extracted_phones:
            try:
                lookup = lookup_phone_number(num)
            except RuntimeError:
                lookup = {
                    "status": "service_unavailable",
                    "explanation": "The phone reputation database is temporarily unavailable.",
                }
            phone_lookups.append({"phone_number": num, **lookup})

        # Run full message analysis on the extracted text
        analysis = analyze_message(extracted_text, input_method="image_ocr")

        _, active_languages = determine_ocr_language_config()

        return {
            "extracted_text": extracted_text,
            "ocr_engine": "Tesseract",
            "ocr_languages": active_languages,
            "numbers_in_image": phone_lookups,
            "analysis": analysis,
        }
    finally:
        await file.close()


@app.post("/check-number")
def check_number(body: dict):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")
    phone = body.get("phone_number", "")
    if not phone or not str(phone).strip():
        raise HTTPException(status_code=400, detail="phone_number is required.")
    try:
        return lookup_phone_number(str(phone).strip())
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/report")
def report_number(request: Request, body: dict):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")

    # 1. Strict input validation
    raw_phone = body.get("phone_number")
    if raw_phone is None or not isinstance(raw_phone, str) or not raw_phone.strip():
        raise HTTPException(status_code=400, detail="phone_number is required and must be a string.")
    phone = raw_phone.strip()
    if len(phone) > 30:
        raise HTTPException(
            status_code=400,
            detail="phone_number exceeds maximum allowed length of 30 characters.",
        )

    raw_cats = body.get("categories")
    if not isinstance(raw_cats, list) or not raw_cats:
        raise HTTPException(
            status_code=400,
            detail=f"categories must be a non-empty list. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}.",
        )
    if len(raw_cats) > 10:
        raise HTTPException(
            status_code=400,
            detail="At most 10 categories can be submitted per report.",
        )
    for c in raw_cats:
        if not isinstance(c, str):
            raise HTTPException(
                status_code=400,
                detail="Each category in categories must be a string.",
            )

    raw_evidence = body.get("evidence_note")
    if raw_evidence is not None and not isinstance(raw_evidence, str):
        raise HTTPException(status_code=400, detail="evidence_note must be a string.")
    if raw_evidence and len(raw_evidence) > 1000:
        raise HTTPException(
            status_code=400,
            detail="evidence_note exceeds maximum allowed length of 1000 characters.",
        )
    evidence = str(raw_evidence or "")[:500]

    # 2. Rate limiting check (protects submission/DB operations)
    client_ip = get_client_ip(request)
    is_allowed, retry_after = report_rate_limiter.check(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many reports submitted. Please wait before submitting again.",
            headers={"Retry-After": str(retry_after)},
        )

    # 3. Submit report with reporter identification for deduplication
    try:
        result = submit_report(phone, raw_cats, evidence, reporter_id=client_ip)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if result["status"] in {"invalid_number", "invalid_categories"}:
        raise HTTPException(status_code=400, detail=result["explanation"])
    return result


@app.post("/dispute")
def dispute_number(request: Request, body: dict):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")

    # 1. Strict input validation
    raw_phone = body.get("phone_number")
    if raw_phone is None or not isinstance(raw_phone, str) or not raw_phone.strip():
        raise HTTPException(
            status_code=400,
            detail="phone_number is required and must be a string.",
        )
    phone = raw_phone.strip()
    if len(phone) > 30:
        raise HTTPException(
            status_code=400,
            detail="phone_number exceeds maximum allowed length of 30 characters.",
        )

    raw_explanation = body.get("explanation")
    if raw_explanation is None or not isinstance(raw_explanation, str) or not raw_explanation.strip():
        raise HTTPException(
            status_code=400,
            detail="explanation is required and must be a string.",
        )
    explanation = raw_explanation.strip()
    if len(explanation) < 10:
        raise HTTPException(
            status_code=400,
            detail="explanation must be at least 10 characters long.",
        )
    if len(explanation) > 1000:
        raise HTTPException(
            status_code=400,
            detail="explanation exceeds maximum allowed length of 1000 characters.",
        )

    raw_contact = body.get("contact_info")
    if raw_contact is not None:
        if not isinstance(raw_contact, str):
            raise HTTPException(
                status_code=400,
                detail="contact_info must be a string.",
            )
        contact_info = raw_contact.strip()
        if len(contact_info) > 254:
            raise HTTPException(
                status_code=400,
                detail="contact_info exceeds maximum allowed length of 254 characters.",
            )
    else:
        contact_info = None

    # 2. Rate limiting check (protects submission and database)
    client_ip = get_client_ip(request)
    is_allowed, retry_after = dispute_rate_limiter.check(client_ip)
    if not is_allowed:
        raise HTTPException(
            status_code=429,
            detail="Too many disputes submitted. Please wait before submitting again.",
            headers={"Retry-After": str(retry_after)},
        )

    # 3. Submit dispute (never logs contact info or explanation)
    try:
        result = submit_dispute(
            phone=phone,
            explanation=explanation,
            contact_info=contact_info,
            reporter_id=client_ip,
        )
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

    if result["status"] == "invalid_number":
        raise HTTPException(status_code=400, detail=result["explanation"])
    if result["status"] == "invalid_explanation":
        raise HTTPException(status_code=400, detail=result["explanation"])

    return result


@app.get("/reported-numbers")
def list_reported_numbers(
    limit: int = 20,
    offset: int = 0,
    search: str | None = None,
):
    try:
        return get_reported_numbers(limit=limit, offset=offset, query=search)
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Bank Security Operations Feed ─────────────────────────────────────────────

@app.get("/security-feed")
def read_security_feed(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    event_type: str | None = None,
    priority: str | None = None,
    review_status: str | None = None,
    mask_phone: bool = False,
    analyst: SecurityAnalyst = Depends(require_analyst_role),
):
    try:
        feed = get_security_feed(
            limit=limit,
            offset=offset,
            event_type=event_type,
            priority=priority,
            review_status=review_status,
            mask_phone=mask_phone,
        )
        return {
            "organization": analyst.organization,
            "analyst_org": analyst.organization,
            "analyst_id": analyst.analyst_id,
            "caller_role": analyst.role,
            "analyst_role": analyst.role,
            **feed,
        }
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.get("/security-feed/{event_id}")
def read_security_feed_event(
    event_id: str,
    mask_phone: bool = False,
    analyst: SecurityAnalyst = Depends(require_analyst_role),
):
    try:
        event = get_security_feed_event(event_id, mask_phone=mask_phone)
        if event is None:
            raise HTTPException(status_code=404, detail="Security feed event not found.")
        return {
            "organization": analyst.organization,
            "analyst_org": analyst.organization,
            "caller_role": analyst.role,
            "analyst_role": analyst.role,
            "event": event,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/security-feed/{event_id}/acknowledge")
def acknowledge_security_feed_event(
    event_id: str,
    body: dict,
    analyst: SecurityAnalyst = Depends(require_analyst_role),
):
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")

    raw_status = body.get("review_status") or body.get("status") or "acknowledged"
    if not isinstance(raw_status, str):
        raise HTTPException(status_code=400, detail="review_status must be a string.")

    raw_notes = body.get("notes") or body.get("analyst_notes")
    if raw_notes is not None and not isinstance(raw_notes, str):
        raise HTTPException(status_code=400, detail="notes must be a string.")

    try:
        updated = update_feed_event_status(
            event_id=event_id,
            new_status=raw_status,
            analyst_id=analyst.analyst_id,
            notes=raw_notes,
        )
        return {
            "message": f"Security feed event status updated to '{raw_status}'.",
            "organization": analyst.organization,
            "analyst_org": analyst.organization,
            "acknowledged_by": analyst.analyst_id,
            "event": updated,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Security feed event not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


# ── Dispute Moderation Endpoints (Analyst / Admin) ────────────────────────────

@app.get("/admin/disputes")
def list_disputes_for_moderation(
    limit: int = Query(20, ge=1, le=100),
    offset: int = Query(0, ge=0),
    status: str | None = None,
    analyst: SecurityAnalyst = Depends(require_analyst_role),
):
    """Retrieve queued reputation disputes for administrative review."""
    try:
        data = get_disputes(limit=limit, offset=offset, review_status=status)
        return {
            "organization": analyst.organization,
            "analyst_id": analyst.analyst_id,
            **data,
        }
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))


@app.post("/admin/disputes/{dispute_id}/status")
def update_dispute_review_status(
    dispute_id: int,
    body: dict,
    analyst: SecurityAnalyst = Depends(require_analyst_role),
):
    """Update review status of a queued reputation dispute."""
    if not isinstance(body, dict):
        raise HTTPException(status_code=400, detail="Invalid request body.")

    raw_status = body.get("review_status") or body.get("status")
    if not raw_status or not isinstance(raw_status, str):
        raise HTTPException(status_code=400, detail="review_status is required and must be a string.")

    try:
        updated = update_dispute_status(dispute_id=dispute_id, new_status=raw_status)
        return {
            "message": f"Dispute status updated to '{raw_status}'.",
            "updated_by": analyst.analyst_id,
            "dispute": updated,
        }
    except KeyError:
        raise HTTPException(status_code=404, detail="Dispute not found.")
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))
    except ValueError as exc:
        raise HTTPException(status_code=400, detail=str(exc))
    except RuntimeError as exc:
        raise HTTPException(status_code=503, detail=str(exc))

