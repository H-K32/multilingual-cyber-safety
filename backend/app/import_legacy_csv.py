# backend/app/import_legacy_csv.py
"""Utility script to import legacy phone reports from CSV into PostgreSQL.

Reads `backend/data/reported_phone_numbers.csv` and safely inserts reports into
`phone_report_submissions` and upserts `phone_number_summary`.

Idempotent: safe to run multiple times without duplicating report counts.
"""

import csv
import logging
import sys
from datetime import date
from pathlib import Path

from backend.app import db
from backend.app.phone_reputation import (
    ALLOWED_CATEGORIES,
    normalize_phone_number,
)

logger = logging.getLogger("import_legacy_csv")
logging.basicConfig(level=logging.INFO, format="%(levelname)s: %(message)s")

CSV_PATH = Path(__file__).resolve().parents[1] / "data" / "reported_phone_numbers.csv"


def import_legacy_reports(csv_path: Path = CSV_PATH) -> int:
    """Import reports from the given CSV file into PostgreSQL.

    Returns the number of imported records.
    """
    if not csv_path.exists():
        logger.warning("CSV file not found: %s", csv_path)
        return 0

    imported_count = 0

    with csv_path.open(encoding="utf-8", newline="") as f:
        reader = csv.DictReader(f)
        with db.get_connection() as conn:
            for row in reader:
                raw_phone = row.get("phone_number", "").strip()
                normalized, country_code = normalize_phone_number(raw_phone)
                if not normalized:
                    logger.warning("Skipping invalid phone number in CSV: %s", raw_phone)
                    continue

                raw_cats = [
                    c.strip().lower()
                    for c in row.get("categories", "").split("|")
                    if c.strip().lower() in ALLOWED_CATEGORIES
                ]
                if not raw_cats:
                    raw_cats = ["other"]

                try:
                    report_count = max(1, int(row.get("report_count", 1)))
                except ValueError:
                    report_count = 1

                source = row.get("source", "").strip() or "legacy csv import"
                v_status = row.get("verification_status", "").strip()
                if v_status not in {"verified", "unverified"}:
                    v_status = "unverified"

                evidence = row.get("evidence_note", "").strip()[:500] or None
                first_rep = row.get("first_reported", "").strip() or date.today().isoformat()
                last_rep = row.get("last_reported", "").strip() or date.today().isoformat()

                # Insert submission record
                conn.execute(
                    """
                    INSERT INTO phone_report_submissions
                        (phone_e164, country_code, categories, evidence_note,
                         source, verification_status)
                    VALUES (%s, %s, %s, %s, %s, %s)
                    """,
                    (normalized, country_code or "", raw_cats, evidence, source, v_status),
                )

                # Upsert into summary
                conn.execute(
                    """
                    INSERT INTO phone_number_summary
                        (phone_e164, country_code, report_count, categories,
                         source, first_reported, last_reported,
                         verification_status, evidence_note)
                    VALUES (%s, %s, %s, %s, %s, %s::DATE, %s::DATE, %s, %s)
                    ON CONFLICT (phone_e164) DO UPDATE SET
                        report_count = phone_number_summary.report_count + EXCLUDED.report_count,
                        categories   = (
                            SELECT array_agg(DISTINCT c ORDER BY c)
                            FROM unnest(
                                phone_number_summary.categories ||
                                EXCLUDED.categories
                            ) AS c
                        ),
                        last_reported = GREATEST(phone_number_summary.last_reported, EXCLUDED.last_reported),
                        evidence_note = COALESCE(
                            EXCLUDED.evidence_note,
                            phone_number_summary.evidence_note
                        ),
                        updated_at   = now()
                    """,
                    (
                        normalized,
                        country_code or "",
                        report_count,
                        raw_cats,
                        source,
                        first_rep,
                        last_rep,
                        v_status,
                        evidence,
                    ),
                )
                imported_count += 1

            conn.commit()

    logger.info("Successfully imported %d legacy report(s).", imported_count)
    return imported_count


if __name__ == "__main__":
    try:
        db.init_db()
        count = import_legacy_reports()
        print(f"Imported {count} records successfully.")
    except Exception as exc:
        print(f"Error during legacy import: {exc}", file=sys.stderr)
        sys.exit(1)
