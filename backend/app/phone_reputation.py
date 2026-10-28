# backend/app/phone_reputation.py
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


def submit_report(
    phone: str,
    categories: List[str],
    evidence_note: str,
) -> dict:
    """Record a community report in PostgreSQL.

    Inserts one row into phone_report_submissions and upserts the aggregated
    summary in phone_number_summary using a single transaction.  Concurrent
    submissions for the same number are handled safely by the ON CONFLICT
    clause — no application-level read-modify-write race condition.

    Signature and return format are identical to the previous CSV version.
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

    try:
        with get_connection() as conn:
            # 1. Record the individual submission.
            conn.execute(
                """
                INSERT INTO phone_report_submissions
                    (phone_e164, country_code, categories, evidence_note,
                     source, verification_status)
                VALUES (%s, %s, %s, %s, 'community submission', 'unverified')
                """,
                (normalized, country_code or "", clean_cats, safe_note),
            )

            # 2. Upsert the summary row.
            #    ON CONFLICT handles concurrent inserts for the same number
            #    without a separate SELECT first.
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
