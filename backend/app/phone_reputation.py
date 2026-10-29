# backend/app/phone_reputation.py
import hashlib
import os
import re
from datetime import date
from typing import List

import phonenumbers
from phonenumbers import PhoneNumberFormat

from backend.app.db import get_connection


# ---------------------------------------------------------------------------
# Known official sender identities
# Maps a canonical sender label (shortcode or name) to the set of numbers /
# shortcodes that are legitimately used by that organisation.  Values are
# lower-cased for case-insensitive matching.
# ---------------------------------------------------------------------------
KNOWN_OFFICIAL_SENDERS: dict[str, dict] = {
    "994": {
        "organisation": "Ethio Telecom",
        "legitimate_ids": {"994"},
        "note": "Ethio Telecom customer service shortcode.",
    },
    "ethiotelecom": {
        "organisation": "Ethio Telecom",
        "legitimate_ids": {"994", "ethiotelecom"},
        "note": "Ethio Telecom branded sender name.",
    },
    "telebirr": {
        "organisation": "Ethio Telecom / telebirr",
        "legitimate_ids": {"994", "telebirr", "6969"},
        "note": "telebirr mobile wallet service.",
    },
    "cbe": {
        "organisation": "Commercial Bank of Ethiopia",
        "legitimate_ids": {"cbe", "8397", "combanketh"},
        "note": "CBE official shortcodes and sender names.",
    },
    "awash": {
        "organisation": "Awash Bank",
        "legitimate_ids": {"awash", "awashbank"},
        "note": "Awash Bank official sender names.",
    },
    "dashen": {
        "organisation": "Dashen Bank",
        "legitimate_ids": {"dashen", "dashenbank"},
        "note": "Dashen Bank official sender names.",
    },
}

# Regex to extract phone-number-like tokens from free text
_PHONE_TOKEN_PATTERN = re.compile(
    r"(?:(?:\+|00)?251[\s.-]?[79][0-9][\s.-]?[0-9]{3}[\s.-]?[0-9]{4}"
    r"|0[79][0-9][\s.-]?[0-9]{3}[\s.-]?[0-9]{4})"
)

SEPARATOR_PATTERN = re.compile(r"[\s().-]")
PHONE_NUMBER_PATTERN = re.compile(r"^\+?[0-9]+$")

ALLOWED_CATEGORIES = {
    "scam",
    "spam_calls",
    "phishing",
    "impersonation",
    "unwanted_marketing",
    "other",
}


# ---------------------------------------------------------------------------
# Pure helper functions — no I/O, signatures unchanged
# ---------------------------------------------------------------------------

def normalize_phone_number(value: str | None) -> tuple[str | None, str | None]:
    if not value or not value.strip():
        return None, None

    cleaned = SEPARATOR_PATTERN.sub("", value.strip())
    if cleaned.startswith("00"):
        cleaned = f"+{cleaned[2:]}"
    if not PHONE_NUMBER_PATTERN.fullmatch(cleaned):
        return None, None

    region = None
    if not cleaned.startswith("+"):
        if not re.fullmatch(r"0[79][0-9]{8}", cleaned):
            return None, None
        region = "ET"
    elif cleaned.startswith("+2510"):
        return None, None

    try:
        parsed = phonenumbers.parse(cleaned, region)
    except phonenumbers.NumberParseException:
        return None, None

    if not phonenumbers.is_valid_number(parsed):
        return None, None

    return (
        phonenumbers.format_number(parsed, PhoneNumberFormat.E164),
        str(parsed.country_code),
    )


def extract_phone_numbers_from_text(text: str) -> list[str]:
    """Return a deduplicated list of E.164-normalised Ethiopian phone numbers
    found in *text*.  Tokens that fail validation are silently dropped."""
    seen: list[str] = []
    for raw in _PHONE_TOKEN_PATTERN.findall(text):
        normalised, _ = normalize_phone_number(raw)
        if normalised and normalised not in seen:
            seen.append(normalised)
    return seen


def verify_sender_identity(
    actual_sender: str | None,
    claimed_identity: str | None,
) -> dict:
    """Check whether *actual_sender* is a legitimate origin for *claimed_identity*.

    Parameters
    ----------
    actual_sender:
        The number or shortcode the message actually arrived from (e.g. the
        number shown in the SMS thread header).
    claimed_identity:
        The organisation or shortcode the message *claims* to represent (e.g.
        "994", "telebirr", "CBE").  Derived from message content or user input.

    Returns a dict with keys:
        status          – "match" | "mismatch" | "unknown_identity" | "not_checked"
        explanation     – human-readable explanation
        risk_indicator  – bool, True when a mismatch is detected
    """
    if not actual_sender or not actual_sender.strip():
        return {
            "status": "not_checked",
            "explanation": "No actual sender was provided; identity verification was skipped.",
            "risk_indicator": False,
        }
    if not claimed_identity or not claimed_identity.strip():
        return {
            "status": "not_checked",
            "explanation": "No claimed identity was provided; identity verification was skipped.",
            "risk_indicator": False,
        }

    key = claimed_identity.strip().lower()
    entry = KNOWN_OFFICIAL_SENDERS.get(key)
    if entry is None:
        return {
            "status": "unknown_identity",
            "explanation": (
                f"'{claimed_identity}' is not in the list of known official senders. "
                "The claim cannot be verified or refuted."
            ),
            "risk_indicator": False,
        }

    actual_lower = actual_sender.strip().lower()
    normalised, _ = normalize_phone_number(actual_sender)
    candidates = {actual_lower}
    if normalised:
        candidates.add(normalised.lower())

    if candidates & entry["legitimate_ids"]:
        return {
            "status": "match",
            "organisation": entry["organisation"],
            "explanation": (
                f"The actual sender '{actual_sender}' matches a known legitimate "
                f"identifier for {entry['organisation']}."
            ),
            "risk_indicator": False,
        }

    return {
        "status": "mismatch",
        "organisation": entry["organisation"],
        "explanation": (
            f"The message claims to be from {entry['organisation']} ({claimed_identity}), "
            f"but the actual sender '{actual_sender}' is not a recognised identifier for "
            f"that organisation. This is suspicious but not definitive proof of fraud."
        ),
        "risk_indicator": True,
    }


# ---------------------------------------------------------------------------
# Database-backed storage functions
# ---------------------------------------------------------------------------

def lookup_phone_number(value: str | None) -> dict:
    """Look up a phone number in the PostgreSQL summary table.

    Signature and return format are identical to the previous CSV version.
    """
    if value is None or not value.strip():
        return {
            "status": "not_provided",
            "explanation": "No sender phone number was provided; number lookup was skipped.",
        }

    normalized_number, country_code = normalize_phone_number(value)
    if normalized_number is None:
        return {
            "status": "invalid_number",
            "explanation": (
                "The supplied sender phone number could not be validated; no reputation "
                "lookup was performed."
            ),
        }

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT report_count, categories, source,
                       first_reported, last_reported,
                       verification_status, evidence_note
                FROM phone_number_summary
                WHERE phone_e164 = %s
                """,
                (normalized_number,),
            ).fetchone()
    except Exception:
        # Do not leak DB internals to callers; surface a safe error.
        raise RuntimeError(
            "The phone reputation database is temporarily unavailable."
        )

    if row is None:
        return {
            "status": "no_reports_found",
            "country_code": country_code,
            "explanation": (
                "No matching reports were found in the local dataset. A lack of reports "
                "does not establish that a number is safe."
            ),
        }

    (
        report_count,
        categories,
        source,
        first_reported,
        last_reported,
        verification_status,
        evidence_note,
    ) = row

    # Normalise types coming from psycopg3 (dates arrive as date objects or str).
    first_reported_str = (
        first_reported.isoformat()
        if hasattr(first_reported, "isoformat")
        else (str(first_reported) if first_reported else None)
    )
    last_reported_str = (
        last_reported.isoformat()
        if hasattr(last_reported, "isoformat")
        else (str(last_reported) if last_reported else None)
    )
    # categories is a PostgreSQL TEXT[] — psycopg3 returns it as a Python list.
    categories_list = list(categories) if categories else []

    qualification = (
        "These reports are verified records; they are evidence to review, not proof that "
        "the number is malicious."
        if verification_status == "verified"
        else "These are unverified community reports and do not confirm that the number is malicious."
    )
    return {
        "status": "reported",
        "country_code": country_code,
        "report_count": report_count,
        "categories": categories_list,
        "source": source,
        "first_reported": first_reported_str,
        "last_reported": last_reported_str,
        "verification_status": verification_status,
        "evidence_note": evidence_note,
        "explanation": (
            f"{report_count} local report(s) were found "
            f"({verification_status}). {qualification}"
        ),
    }


def compute_reporter_hash(reporter_id: str | None) -> str | None:
    """Generate a salted cryptographic SHA-256 hash of the reporter ID.

    Uses a server-side salt (from DAGU_HASH_SALT or internal default) to protect
    client IP addresses against offline rainbow-table deanonymization attacks.
    """
    if not reporter_id or not str(reporter_id).strip():
        return None
    salt = os.environ.get("DAGU_HASH_SALT", "dagu_default_secure_salt_v1")
    payload = f"{salt}:{reporter_id.strip()}"
    return hashlib.sha256(payload.encode("utf-8")).hexdigest()


def submit_report(
    phone: str,
    categories: List[str],
    evidence_note: str,
    reporter_id: str | None = None,
) -> dict:
    """Record a community report in PostgreSQL.

    Inserts one row into phone_report_submissions and upserts the aggregated
    summary in phone_number_summary using a single transaction.  Concurrent
    submissions for the same number are handled safely by the ON CONFLICT
    clause — no application-level read-modify-write race condition.

    If reporter_id is provided, duplicate submissions from the same reporter
    within a 24-hour window update categories without inflating the report count.

    All submitted reports are stored as unverified.
    """
    normalized, country_code = normalize_phone_number(phone)
    if normalized is None:
        return {
            "status": "invalid_number",
            "explanation": "The supplied phone number could not be validated.",
        }

    clean_cats = [
        c.strip().lower() for c in categories if c.strip().lower() in ALLOWED_CATEGORIES
    ]
    if not clean_cats:
        return {
            "status": "invalid_categories",
            "explanation": (
                f"No valid categories supplied. Allowed: {', '.join(sorted(ALLOWED_CATEGORIES))}."
            ),
        }

    # Truncate evidence note to 500 chars; strip newlines.
    safe_note = evidence_note.replace("\n", " ").replace("\r", " ")[:500].strip() or None

    reporter_hash = compute_reporter_hash(reporter_id)

    try:
        with get_connection() as conn:
            # Check for duplicate submission from this reporter within 24 hours
            if reporter_hash:
                dup_row = conn.execute(
                    """
                    SELECT id FROM phone_report_submissions
                    WHERE phone_e164 = %s
                      AND reporter_hash = %s
                      AND submitted_at >= (now() - INTERVAL '24 hours')
                    LIMIT 1
                    """,
                    (normalized, reporter_hash),
                ).fetchone()

                if dup_row is not None:
                    # Do not increment report count; merge any new categories
                    conn.execute(
                        """
                        UPDATE phone_number_summary SET
                            categories    = (
                                SELECT array_agg(DISTINCT c ORDER BY c)
                                FROM unnest(
                                    phone_number_summary.categories ||
                                    %s::TEXT[]
                                ) AS c
                            ),
                            last_reported = CURRENT_DATE,
                            evidence_note = COALESCE(%s, phone_number_summary.evidence_note),
                            updated_at    = now()
                        WHERE phone_e164 = %s
                        """,
                        (clean_cats, safe_note, normalized),
                    )
                    conn.commit()
                    return {
                        "status": "already_reported",
                        "explanation": (
                            f"A report for this number was already recorded from your client within the last 24 hours. "
                            "The report count was not incremented to prevent duplicate inflation."
                        ),
                    }

            # 1. Record the individual submission.
            conn.execute(
                """
                INSERT INTO phone_report_submissions
                    (phone_e164, country_code, categories, evidence_note,
                     source, verification_status, reporter_hash)
                VALUES (%s, %s, %s, %s, 'community submission', 'unverified', %s)
                """,
                (normalized, country_code or "", clean_cats, safe_note, reporter_hash),
            )

            # 2. Upsert the summary row.
            result = conn.execute(
                """
                INSERT INTO phone_number_summary
                    (phone_e164, country_code, report_count, categories,
                     source, first_reported, last_reported,
                     verification_status, evidence_note)
                VALUES (%s, %s, 1, %s,
                        'community submission', CURRENT_DATE, CURRENT_DATE,
                        'unverified', %s)
                ON CONFLICT (phone_e164) DO UPDATE SET
                    report_count  = phone_number_summary.report_count + 1,
                    categories    = (
                        SELECT array_agg(DISTINCT c ORDER BY c)
                        FROM unnest(
                            phone_number_summary.categories ||
                            EXCLUDED.categories
                        ) AS c
                    ),
                    last_reported = CURRENT_DATE,
                    evidence_note = COALESCE(
                        EXCLUDED.evidence_note,
                        phone_number_summary.evidence_note
                    ),
                    updated_at    = now()
                RETURNING
                    report_count,
                    (xmax::text = '0') AS is_insert
                """,
                (normalized, country_code or "", clean_cats, safe_note),
            ).fetchone()

            conn.commit()

        report_count, is_insert = result
        if bool(is_insert):
            return {
                "status": "submitted",
                "explanation": (
                    "Your report has been recorded as an unverified community submission. "
                    "It does not confirm that the number is malicious."
                ),
            }
        return {
            "status": "updated",
            "explanation": (
                f"An existing record for this number was updated. "
                f"Report count is now {report_count}. "
                "This is an unverified community submission."
            ),
        }

    except Exception:
        raise RuntimeError(
            "The phone reputation database is temporarily unavailable."
        )


def mask_phone_number(phone_e164: str) -> str:
    """Mask phone number to protect reporter and community privacy.

    Examples:
    +251911234567 -> +251 9XX XXX XXX
    +251711234567 -> +251 7XX XXX XXX
    """
    if not phone_e164 or not phone_e164.strip():
        return ""
    cleaned = phone_e164.strip()
    if cleaned.startswith("+251") and len(cleaned) == 13:
        op = cleaned[4]  # '9' or '7'
        return f"+251 {op}XX XXX XXX"
    if cleaned.startswith("+"):
        prefix = cleaned[:4]
        return f"{prefix} XXX XXX"
    return "XXXX XXX XXX"


def derive_risk_status(
    report_count: int,
    verification_status: str,
    categories: list[str],
) -> tuple[str, str]:
    """Derive human-readable risk status and machine token based on real reports.

    Returns (risk_level, risk_status):
    - ("High Risk", "HIGH_RISK")
    - ("Suspicious", "SUSPICIOUS")
    - ("Reported", "REPORTED")
    """
    if verification_status == "verified" or report_count >= 10:
        return "High Risk", "HIGH_RISK"
    elif report_count >= 3 or any(
        c in {"scam", "phishing", "impersonation"} for c in categories
    ):
        return "Suspicious", "SUSPICIOUS"
    else:
        return "Reported", "REPORTED"


def get_reported_numbers(
    limit: int = 20,
    offset: int = 0,
    query: str | None = None,
) -> dict:
    """Fetch distinct reported numbers from phone_number_summary.

    Only public fields are returned (phone number masked for privacy, report count,
    categories, verification status, dates). Private notes and sources are excluded.
    Ordered by highest report count first.
    """
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)
    clean_query = query.strip() if query and query.strip() else None

    # Handle local leading 0 for Ethiopian phone searches (e.g. "0911" -> "911")
    search_alt = clean_query[1:] if clean_query and clean_query.startswith("0") and len(clean_query) > 1 else clean_query

    try:
        with get_connection() as conn:
            if clean_query:
                param_pattern = f"%{clean_query}%"
                param_alt = f"%{search_alt}%"
                count_sql = """
                    SELECT count(*)
                    FROM phone_number_summary
                    WHERE phone_e164 ILIKE %s OR phone_e164 ILIKE %s OR categories::text ILIKE %s
                """
                total = conn.execute(count_sql, (param_pattern, param_alt, param_pattern)).fetchone()[0]

                data_sql = """
                    SELECT phone_e164, country_code, report_count, categories,
                           first_reported, last_reported, verification_status
                    FROM phone_number_summary
                    WHERE phone_e164 ILIKE %s OR phone_e164 ILIKE %s OR categories::text ILIKE %s
                    ORDER BY report_count DESC, last_reported DESC, phone_e164 ASC
                    LIMIT %s OFFSET %s
                """
                rows = conn.execute(
                    data_sql, (param_pattern, param_alt, param_pattern, safe_limit, safe_offset)
                ).fetchall()
            else:
                count_sql = "SELECT count(*) FROM phone_number_summary"
                total = conn.execute(count_sql).fetchone()[0]

                data_sql = """
                    SELECT phone_e164, country_code, report_count, categories,
                           first_reported, last_reported, verification_status
                    FROM phone_number_summary
                    ORDER BY report_count DESC, last_reported DESC, phone_e164 ASC
                    LIMIT %s OFFSET %s
                """
                rows = conn.execute(data_sql, (safe_limit, safe_offset)).fetchall()

    except Exception:
        raise RuntimeError("The phone reputation database is temporarily unavailable.")

    items = []
    for row in rows:
        (
            phone_e164,
            country_code,
            report_count,
            categories,
            first_reported,
            last_reported,
            verification_status,
        ) = row

        cats = list(categories) if categories else []
        risk_level, risk_status = derive_risk_status(
            report_count, verification_status, cats
        )
        first_rep_str = (
            first_reported.isoformat()
            if hasattr(first_reported, "isoformat")
            else (str(first_reported) if first_reported else None)
        )
        last_rep_str = (
            last_reported.isoformat()
            if hasattr(last_reported, "isoformat")
            else (str(last_reported) if last_reported else None)
        )

        items.append({
            "phone_number": phone_e164,
            "masked_phone": mask_phone_number(phone_e164),
            "country_code": country_code,
            "report_count": report_count,
            "categories": cats,
            "risk_level": risk_level,
            "risk_status": risk_status,
            "verification_status": verification_status,
            "first_reported": first_rep_str,
            "last_reported": last_rep_str,
        })

    return {
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "has_more": (safe_offset + len(items)) < total,
        "items": items,
    }


def submit_dispute(
    phone: str,
    explanation: str,
    contact_info: str | None = None,
    reporter_id: str | None = None,
) -> dict:
    """Record a dispute against a phone number's reputation in PostgreSQL.

    Disputes allow legitimate owners or users to contest inaccurate status
    (e.g. recycled numbers, telecom spoofing victims, official numbers).

    Submitting a dispute queues the record for administrative review.
    CRITICAL: It DOES NOT automatically delete community reports, reset
    report counts, or mark the number safe. Existing community reports remain
    visible to protect users until the dispute is reviewed.

    Personal contact information and explanation text are stored exclusively in
    the phone_number_disputes table and are NEVER exposed via public lookup
    endpoints (such as /check-number or /reported-numbers) or application logs.
    """
    normalized, country_code = normalize_phone_number(phone)
    if normalized is None:
        return {
            "status": "invalid_number",
            "explanation": "The supplied phone number could not be validated.",
        }

    clean_explanation = explanation.strip() if explanation else ""
    if len(clean_explanation) < 10 or len(clean_explanation) > 1000:
        return {
            "status": "invalid_explanation",
            "explanation": "Explanation must be between 10 and 1000 characters.",
        }

    clean_contact = (
        contact_info.strip()[:254]
        if contact_info and str(contact_info).strip()
        else None
    )

    reporter_hash = compute_reporter_hash(reporter_id)

    try:
        with get_connection() as conn:
            conn.execute(
                """
                INSERT INTO phone_number_disputes
                    (phone_e164, country_code, explanation, contact_info,
                     review_status, reporter_hash)
                VALUES (%s, %s, %s, %s, 'pending', %s)
                """,
                (
                    normalized,
                    country_code or "",
                    clean_explanation,
                    clean_contact,
                    reporter_hash,
                ),
            )
            conn.commit()

        return {
            "status": "dispute_recorded",
            "phone_number": normalized,
            "review_status": "pending",
            "explanation": (
                "Your dispute has been recorded and queued for moderation review. "
                "Existing community reports remain visible until the dispute is reviewed."
            ),
        }
    except Exception:
        raise RuntimeError(
            "The phone reputation database is temporarily unavailable."
        )


def get_disputes(
    limit: int = 20,
    offset: int = 0,
    review_status: str | None = None,
) -> dict:
    """List disputes with pagination and optional status filter (admin/analyst use only)."""
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)

    where_clauses = []
    params: list = []
    if review_status and review_status.strip():
        where_clauses.append("review_status = %s")
        params.append(review_status.strip().lower())

    where_sql = f"WHERE {' AND '.join(where_clauses)}" if where_clauses else ""

    try:
        with get_connection() as conn:
            count_cur = conn.execute(
                f"SELECT count(*) FROM phone_number_disputes {where_sql}",
                tuple(params),
            )
            count_row = count_cur.fetchone() if count_cur else None
            total = count_row[0] if count_row else 0

            cur = conn.execute(
                f"""
                SELECT id, phone_e164, country_code, explanation, contact_info,
                       review_status, submitted_at
                FROM phone_number_disputes
                {where_sql}
                ORDER BY submitted_at DESC
                LIMIT %s OFFSET %s
                """,
                tuple(params + [safe_limit, safe_offset]),
            )
            rows = cur.fetchall() or []

            items = []
            for r in rows:
                items.append({
                    "id": r[0],
                    "phone_number": r[1],
                    "country_code": r[2],
                    "explanation": r[3],
                    "contact_info": r[4],
                    "review_status": r[5],
                    "submitted_at": r[6].isoformat() if hasattr(r[6], "isoformat") else str(r[6]),
                })

            return {
                "total": total,
                "limit": safe_limit,
                "offset": safe_offset,
                "has_more": (safe_offset + len(items)) < total,
                "items": items,
            }
    except Exception:
        raise RuntimeError(
            "The phone reputation database is temporarily unavailable."
        )


def update_dispute_status(
    dispute_id: int,
    new_status: str,
) -> dict:
    """Update review status of a dispute ('pending', 'under_review', 'resolved', 'rejected')."""
    valid_statuses = {"pending", "under_review", "resolved", "rejected"}
    clean_status = new_status.strip().lower() if new_status else ""
    if clean_status not in valid_statuses:
        raise ValueError(
            f"Invalid review_status '{new_status}'. Allowed: {', '.join(sorted(valid_statuses))}."
        )

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE phone_number_disputes
                SET review_status = %s
                WHERE id = %s
                RETURNING id, phone_e164, review_status
                """,
                (clean_status, dispute_id),
            )
            row = cur.fetchone()
            if row is None:
                raise KeyError(f"Dispute with ID {dispute_id} not found.")
            conn.commit()
            return {
                "id": row[0],
                "phone_number": row[1],
                "review_status": row[2],
            }
    except (KeyError, ValueError):
        raise
    except Exception:
        raise RuntimeError(
            "The phone reputation database is temporarily unavailable."
        )

