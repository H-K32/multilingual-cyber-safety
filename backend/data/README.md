# Local phone reputation dataset

`reported_phone_numbers.csv` is the local, opt-in lookup source. It intentionally
contains only a header and **no phone reports**; no real or synthetic reports
have been invented.

Add one record per number only when the report is properly sourced and its use
is permitted. The lookup normalizes valid international numbers to E.164 before
matching, including Ethiopian local `09…` / `07…` numbers and their `+251…`
equivalents.

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
and `unwanted_marketing`. The app does not scrape or import third-party lists.
Community reports are not proof that a number is malicious; no local match is
not evidence that a number is safe.
