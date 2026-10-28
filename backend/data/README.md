# Local phone reputation dataset (Legacy / Import Source)

> **Notice:** The production data store for phone reputation is **Neon PostgreSQL**
> using the `phone_report_submissions` and `phone_number_summary` tables.
> The CSV file in this directory is preserved only as a documented legacy format
> and optional seed/import source.

`reported_phone_numbers.csv` intentionally contains only a header and **no real phone reports**.

To import legacy records from this CSV into Neon PostgreSQL, run:
```bash
python -m backend.app.import_legacy_csv
```

CSV columns:

| Column | Meaning |
| --- | --- |
| `phone_number` | Valid international number; Ethiopian `+251…` is preferred. |
| `country_code` | Calling code without `+`, such as `251`. |
| `report_count` | Positive count supported by the cited source. |
| `categories` | One or more categories separated by `|` (for example `spam_calls|scam`). |
| `source` | Report source, with enough detail to audit provenance. |
| `first_reported`, `last_reported` | ISO `YYYY-MM-DD` dates, or empty if unavailable. |
| `verification_status` | `verified` or `unverified`; do not imply verification without moderation evidence. |
| `evidence_note` | Short, non-sensitive evidence summary; omit private message contents. |

Supported categories include `scam`, `spam_calls`, `phishing`, `impersonation`,
and `unwanted_marketing`.
