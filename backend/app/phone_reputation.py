import csv
import re
from datetime import date
from pathlib import Path
from typing import List

import phonenumbers
from phonenumbers import PhoneNumberFormat


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


DATASET_PATH = Path(__file__).resolve().parents[1] / "data" / "reported_phone_numbers.csv"
SEPARATOR_PATTERN = re.compile(r"[\s().-]")
PHONE_NUMBER_PATTERN = re.compile(r"^\+?[0-9]+$")


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


def _read_reported_numbers() -> dict[str, dict]:
    reports: dict[str, dict] = {}
    with DATASET_PATH.open(encoding="utf-8", newline="") as dataset:
        for row in csv.DictReader(dataset):
            normalized_number, country_code = normalize_phone_number(
                row["phone_number"]
            )
            if normalized_number is None:
                raise ValueError("Phone reputation dataset contains an invalid number.")
            if row["country_code"].strip() not in {"", country_code}:
                raise ValueError(
                    "Phone reputation dataset contains a mismatched country code."
                )
            if row["verification_status"] not in {"verified", "unverified"}:
                raise ValueError(
                    "Phone reputation dataset contains an unsupported verification status."
                )
            report_count = int(row["report_count"])
            if report_count < 1:
                raise ValueError("Phone reputation report counts must be positive.")
            if not row["source"].strip():
                raise ValueError("Phone reputation records must include a report source.")
            categories = [
                category.strip()
                for category in row["categories"].split("|")
                if category.strip()
            ]
            if not categories:
                raise ValueError("Phone reputation records must include a category.")
            first_reported = row["first_reported"].strip() or None
            last_reported = row["last_reported"].strip() or None
            try:
                if first_reported:
                    date.fromisoformat(first_reported)
                if last_reported:
                    date.fromisoformat(last_reported)
            except ValueError as error:
                raise ValueError(
                    "Phone reputation report dates must use ISO YYYY-MM-DD format."
                ) from error
            if first_reported and last_reported and first_reported > last_reported:
                raise ValueError("First report date must not be after last report date.")
            if normalized_number in reports:
                raise ValueError("Phone reputation dataset contains duplicate numbers.")

            reports[normalized_number] = {
                "report_count": report_count,
                "categories": categories,
                "source": row["source"].strip(),
                "first_reported": first_reported,
                "last_reported": last_reported,
                "verification_status": row["verification_status"],
                "evidence_note": row["evidence_note"].strip() or None,
            }
    return reports


def lookup_phone_number(value: str | None) -> dict:
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

    report = _read_reported_numbers().get(normalized_number)
    if report is None:
        return {
            "status": "no_reports_found",
            "country_code": country_code,
            "explanation": (
                "No matching reports were found in the local dataset. A lack of reports "
                "does not establish that a number is safe."
            ),
        }

    verification_status = report["verification_status"]
    qualification = (
        "These reports are verified records; they are evidence to review, not proof that "
        "the number is malicious."
        if verification_status == "verified"
        else "These are unverified community reports and do not confirm that the number is malicious."
    )
    return {
        "status": "reported",
        "country_code": country_code,
        **report,
        "explanation": (
            f"{report['report_count']} local report(s) were found "
            f"({verification_status}). {qualification}"
        ),
    }


ALLOWED_CATEGORIES = {
    "scam",
    "spam_calls",
    "phishing",
    "impersonation",
    "unwanted_marketing",
    "other",
}


def submit_report(
    phone: str,
    categories: List[str],
    evidence_note: str,
) -> dict:
    """Append a community report to the local dataset.

    Returns a dict with ``status`` and ``explanation``.
    The submitted number is normalized before writing; invalid numbers are
    rejected.  All submitted reports are stored as ``unverified``.
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

    today = date.today().isoformat()
    # Truncate evidence note to 500 chars; strip newlines to keep CSV safe
    safe_note = evidence_note.replace("\n", " ").replace("\r", " ")[:500].strip()

    existing = _read_reported_numbers()
    if normalized in existing:
        # Increment report count and update last_reported; keep existing categories
        rec = existing[normalized]
        merged_cats = list(dict.fromkeys(rec["categories"] + clean_cats))
        new_count = rec["report_count"] + 1
        _rewrite_dataset(
            normalized,
            country_code or "",
            new_count,
            merged_cats,
            rec["source"],
            rec["first_reported"] or today,
            today,
            rec["verification_status"],
            safe_note or rec["evidence_note"] or "",
        )
        return {
            "status": "updated",
            "explanation": (
                f"An existing record for this number was updated. "
                f"Report count is now {new_count}. "
                "This is an unverified community submission."
            ),
        }

    with DATASET_PATH.open("a", encoding="utf-8", newline="") as dataset:
        writer = csv.DictWriter(dataset, fieldnames=[
            "phone_number", "country_code", "report_count", "categories",
            "source", "first_reported", "last_reported",
            "verification_status", "evidence_note",
        ])
        writer.writerow({
            "phone_number": normalized,
            "country_code": country_code or "",
            "report_count": 1,
            "categories": "|".join(clean_cats),
            "source": "community submission",
            "first_reported": today,
            "last_reported": today,
            "verification_status": "unverified",
            "evidence_note": safe_note,
        })

    return {
        "status": "submitted",
        "explanation": (
            "Your report has been recorded as an unverified community submission. "
            "It does not confirm that the number is malicious."
        ),
    }


def _rewrite_dataset(
    normalized: str,
    country_code: str,
    report_count: int,
    categories: List[str],
    source: str,
    first_reported: str,
    last_reported: str,
    verification_status: str,
    evidence_note: str,
) -> None:
    """Rewrite the CSV updating the row for ``normalized``."""
    rows = []
    fieldnames = [
        "phone_number", "country_code", "report_count", "categories",
        "source", "first_reported", "last_reported",
        "verification_status", "evidence_note",
    ]
    with DATASET_PATH.open(encoding="utf-8", newline="") as dataset:
        for row in csv.DictReader(dataset):
            rows.append(row)

    with DATASET_PATH.open("w", encoding="utf-8", newline="") as dataset:
        writer = csv.DictWriter(dataset, fieldnames=fieldnames)
        writer.writeheader()
        for row in rows:
            n, _ = normalize_phone_number(row["phone_number"])
            if n == normalized:
                writer.writerow({
                    "phone_number": normalized,
                    "country_code": country_code,
                    "report_count": report_count,
                    "categories": "|".join(categories),
                    "source": source,
                    "first_reported": first_reported,
                    "last_reported": last_reported,
                    "verification_status": verification_status,
                    "evidence_note": evidence_note,
                })
            else:
                writer.writerow(row)


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
    # Also try the normalised E.164 form so shortcodes and full numbers both match
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
