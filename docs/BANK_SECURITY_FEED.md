# Dagu Bank Security Operations Feed (SOC Feed)

## 1. Overview & Operational Purpose

The **Dagu Bank Security Operations Feed** provides authorized commercial banking and telecom security operations center (SOC) analysts with a real-time, authenticated stream of actionable threat intelligence signals derived from Dagu's crowdsourced community reporting platform.

> [!IMPORTANT]
> **Heuristic Classification & Unverified Notice**
> All threat signals in the feed represent **unverified community submissions** and heuristic pattern detections. They alert financial security teams to emerging social engineering vectors, smishing campaigns, and impersonation attempts targeting their customers. They do **not** constitute confirmed compromise of internal bank infrastructure or verified fraudulent guilt.

---

## 2. Threat Signal Detection Architecture & Data Lineage

The security feed continuously aggregates signals from three foundational data stores into dedicated `security_feed_events`:

```
┌─────────────────────────────────┐
│     phone_report_submissions    │──┐
│  (reporter_hash, created_at)    │  │
└─────────────────────────────────┘  │
                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────┐
│      phone_number_summary       │──►│  sync_security_feed_signals │
│  (report_count, categories)     │   └──────────────┬──────────────┘
└─────────────────────────────────┘                  │
                                                     ▼
┌─────────────────────────────────┐   ┌─────────────────────────────┐
│      phone_number_disputes      │──►│    security_feed_events     │
│   (review_status: pending)      │   │  (deterministic alert IDs)  │
└─────────────────────────────────┘   └─────────────────────────────┘
```

### Signal Detection Heuristics

| Signal Name | Event Type | Trigger Criteria | Priority |
| :--- | :--- | :--- | :--- |
| **Reputation Spike** | `reputation_spike` | $\ge 3$ distinct submissions within a rolling 24-hour window | `critical` ($\ge 5$ in 24h) / `high` ($\ge 3$ in 24h) |
| **High Report Volume** | `high_report_volume` | Cumulative volume of $\ge 5$ distinct community reports | `high` |
| **Cross-Category Threat**| `cross_category_threat` | Reports spanning $\ge 2$ distinct threat categories (e.g., `scam` + `phishing`) | `medium` |
| **Disputed Threat** | `disputed_threat` | Reported number ($\ge 2$ reports) with an active community dispute (`pending` or `under_review`) | `medium` |

### Deterministic Alert IDs & State Preservation

Alert IDs are computed deterministically from the signal prefix and the SHA-256 hash of the normalized E.164 phone number:
$$\text{event\_id} = \text{EVT}-\{\text{PREFIX}\}-\text{SHA256}(phone\_e164)[:12].\text{upper}()$$

*Examples:*
- `EVT-SPIKE-4C21625D32FF`
- `EVT-VOL-4C21625D32FF`
- `EVT-XCAT-4C21625D32FF`
- `EVT-DISP-4C21625D32FF`

When `sync_security_feed_signals` executes on incoming reports or feed queries, it uses an idempotent `ON CONFLICT (event_id) DO UPDATE` query that preserves analyst modifications (`acknowledged`, `under_review`, `resolved`, `dismissed`) and attached analyst notes, while updating metric counters (`total_reports`, `reports_last_24h`, `last_updated`).

---

## 3. Review Status Lifecycle

SOC analysts manage the lifecycle of incoming alerts through five structured states:

```
 [ new ] ────────► [ acknowledged ] ────────► [ under_review ]
    │                      │                          │
    ▼                      ▼                          ▼
[ dismissed ]       [ dismissed ]              [ resolved ]
```

1. **`new`**: Newly triggered signal awaiting SOC triage.
2. **`acknowledged`**: Analyst has seen and registered the threat alert.
3. **`under_review`**: Analyst has initiated active fraud/SIM investigation or cross-bank coordination.
4. **`resolved`**: Investigation complete (e.g., number blocked at telco level or cleared).
5. **`dismissed`**: Alert triaged as non-actionable or false lead.

---

## 4. Authentication, Authorization & Key Management

### RBAC Hierarchy

Access to the security feed is strictly restricted to authenticated institutional analysts via role-based access control (RBAC):
- **`analyst`**: Can read feed items, inspect event details, and update review statuses / submit investigation notes.
- **`admin`**: Full access to all feeds, audit metrics, and configuration.
- **`viewer`**: Read-only access to feed items.

### Configuration via `DAGU_SECURITY_FEED_API_KEYS`

API keys are configured server-side via the environment variable `DAGU_SECURITY_FEED_API_KEYS`. It accepts a JSON-formatted mapping of API keys to analyst credentials:

```bash
export DAGU_SECURITY_FEED_API_KEYS='{
  "cbe-soc-secret-token-key-2026": {
    "org": "Commercial Bank of Ethiopia",
    "role": "analyst"
  },
  "telebirr-soc-token-key-2026": {
    "org": "Ethio Telecom Telebirr Fraud Ops",
    "role": "analyst"
  },
  "dagu-admin-ops-key-2026": {
    "org": "Dagu Platform Operations",
    "role": "admin"
  }
}'
```

### Security Properties
1. **Timing-Safe Key Comparison**: Keys are verified using `hmac.compare_digest` across all configured entries, preventing side-channel timing attacks.
2. **Zero Client Spoofing**: Organization name (`analyst_org`) and role (`analyst_role`) are strictly derived server-side from the verified token. Client headers cannot override them.
3. **Transport Security**: Requires `Authorization: Bearer <token>` or `X-API-Key: <token>`.
4. **Fail-Closed Behavior**: If `DAGU_SECURITY_FEED_API_KEYS` is unset or empty, feed endpoints fail closed with HTTP `503 Service Unavailable`.

---

## 5. API Reference

### 1. `GET /security-feed`
Retrieves a paginated list of security threat alerts with optional filtering.

**Headers:**
```http
Authorization: Bearer <analyst_token>
```

**Query Parameters:**
- `event_type` *(optional)*: Filter by `reputation_spike`, `high_report_volume`, `cross_category_threat`, `disputed_threat`.
- `status` *(optional)*: Filter by `new`, `acknowledged`, `under_review`, `resolved`, `dismissed`.
- `priority` *(optional)*: Filter by `critical`, `high`, `medium`, `low`.
- `limit` *(optional, default 50, max 100)*: Items per page.
- `offset` *(optional, default 0)*: Pagination offset.
- `mask_phone` *(optional, default false)*: If true, masks normalized phone numbers.

**Response (`200 OK`):**
```json
{
  "items": [
    {
      "event_id": "EVT-SPIKE-4C21625D32FF",
      "phone_number": "+251 91 123 4567",
      "phone_masked": "+251 91 ••• ••67",
      "event_type": "reputation_spike",
      "priority": "critical",
      "total_reports": 6,
      "reports_last_24h": 6,
      "categories": ["scam", "phishing"],
      "reason": "Sudden surge of 6 reports in the last 24 hours.",
      "evidence_summary": "Recent report spike across multiple distinct reporters.",
      "confidence_limitations": "Heuristic community threat signal. Unverified community submissions.",
      "review_status": "new",
      "analyst_notes": null,
      "last_updated": "2026-10-28T18:00:00Z",
      "created_at": "2026-10-28T18:00:00Z"
    }
  ],
  "total": 1,
  "limit": 50,
  "offset": 0,
  "has_more": false,
  "analyst_org": "Commercial Bank of Ethiopia",
  "analyst_role": "analyst"
}
```

---

### 2. `GET /security-feed/{event_id}`
Retrieves detailed information for a single security alert.

**Response (`200 OK`):**
Returns the single event JSON object with complete audit fields (`acknowledged_by`, `acknowledged_at`).

---

### 3. `POST /security-feed/{event_id}/acknowledge`
Transitions the review status of an alert and logs analyst notes.

**Request Body:**
```json
{
  "status": "under_review",
  "analyst_notes": "SIM card flagged with Ethio Telecom fraud liaison team."
}
```

**Response (`200 OK`):**
```json
{
  "event_id": "EVT-SPIKE-4C21625D32FF",
  "review_status": "under_review",
  "analyst_notes": "SIM card flagged with Ethio Telecom fraud liaison team.",
  "acknowledged_by": "Commercial Bank of Ethiopia (analyst)",
  "acknowledged_at": "2026-10-28T18:15:00Z"
}
```

---

## 6. Privacy & PII Protection Guarantees

The security feed is engineered with zero PII leakage:
1. **Reporter Hashes Redacted**: Salted SHA-256 client hashes (`reporter_hash`) used for rate-limiting and deduplication are strictly confined to internal database tables and **never** returned in the security feed.
2. **Dispute Submitter Protection**: Contact details (emails, phone numbers) and free-text explanations provided in dispute submissions are strictly excluded from the bank feed to protect community members contesting numbers.
3. **Number Masking Available**: Both full normalized E.164 and masked representations (`+251 91 ••• ••67`) are provided, allowing banks to adjust internal logging privacy.

---

## 7. Multi-Tenant Isolation Roadmap

In the current Phase 6 implementation, all authenticated institutional analysts access a unified platform threat feed containing nationwide community alerts.

### Planned Enhancements for Multi-Tenant Segmentation:
1. **Brand-Affinity Routing**: Filter alerts based on claimed sender identities (e.g., messages claiming to originate from "CBE" or "994" routed specifically to Commercial Bank of Ethiopia SOC).
2. **Webhook Subscriptions**: Webhook push notifications delivering `critical` 24h spikes directly to bank SIEM/SOAR platforms (e.g., Splunk, IBM QRadar, Microsoft Sentinel) with HMAC-SHA256 payload signing.
3. **Mutual TLS (mTLS)**: Support for client certificates in enterprise bank datacenter integrations.

