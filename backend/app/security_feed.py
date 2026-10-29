# backend/app/security_feed.py
"""Bank Security Operations Feed for Dagu Cybersecurity Platform.

Generates and delivers actionable threat intelligence signals from existing Dagu
reputation datasets to authorized financial institutions and security analysts.

Supported Signals
-----------------
1. `reputation_spike`: Rapid influx of reports within a 24-hour time window.
2. `high_report_volume`: Significant accumulation of independent community reports.
3. `cross_category_threat`: Multi-vector fraud activity spanning distinct categories.
4. `disputed_threat`: Contested reputation where active reports coexist with a pending dispute.

Privacy & Evidence Governance
------------------------------
- Generates signals strictly from existing reputation data; does not collect private message texts.
- Never exposes reporter identities, SHA-256 reporter hashes, or dispute personal contact info.
- Explicitly flags all signals as unverified community reports, not confirmed bank compromise.
- Alert IDs are deterministic to prevent alert fatigue and duplicate re-alerting.
"""

import hashlib
from datetime import datetime, timezone
from typing import Any, Dict, List, Optional, Tuple

from backend.app.db import get_connection
from backend.app.phone_reputation import mask_phone_number

VALID_EVENT_TYPES = {
    "reputation_spike",
    "high_report_volume",
    "cross_category_threat",
    "disputed_threat",
}

VALID_PRIORITIES = {"LOW", "MEDIUM", "HIGH", "CRITICAL"}

VALID_REVIEW_STATUSES = {
    "new",
    "acknowledged",
    "under_review",
    "resolved",
    "dismissed",
}


def _make_event_id(prefix: str, phone_e164: str) -> str:
    """Generate a deterministic, stable event ID from phone and event type."""
    h = hashlib.sha256(phone_e164.strip().encode("utf-8")).hexdigest()[:12].upper()
    return f"EVT-{prefix.upper()}-{h}"


def sync_security_feed_signals() -> int:
    """Scan existing database records and synchronize security feed events.

    Detects:
    1. High report volume (>= 5 reports or verified) from phone_number_summary.
    2. Cross-category threats (>= 3 categories) from phone_number_summary.
    3. Rapid reputation spikes (>= 3 distinct reporters in last 24h) from phone_report_submissions.
    4. Disputed threats (active reports + pending dispute) from phone_number_disputes.

    Inserts new signals or updates existing counts without overwriting review status or analyst notes.
    Returns the count of synced signals.
    """
    signals: List[Dict[str, Any]] = []

    try:
        with get_connection() as conn:
            # 1. High report volume from phone_number_summary
            cur = conn.execute(
                """
                SELECT phone_e164, country_code, report_count, categories, verification_status
                FROM phone_number_summary
                WHERE report_count >= 5 OR verification_status = 'verified'
                """
            )
            for row in cur.fetchall() or []:
                phone_e164, country_code, report_count, categories, v_status = row
                cats = list(categories) if categories else []
                is_crit = report_count >= 10 or v_status == "verified"
                priority = "CRITICAL" if is_crit else "HIGH"
                event_id = _make_event_id("VOL", phone_e164)
                v_label = "verified threat" if v_status == "verified" else "unverified community records"
                signals.append({
                    "event_id": event_id,
                    "event_type": "high_report_volume",
                    "priority": priority,
                    "phone_e164": phone_e164,
                    "country_code": country_code,
                    "report_count": report_count,
                    "categories": cats,
                    "recent_reports_24h": 0,
                    "reason": f"Accumulated {report_count} independent reports ({v_label}) across categories: {', '.join(sorted(cats))}.",
                    "evidence_source": "Aggregated reputation records in phone_number_summary.",
                    "confidence_qualification": "Community-reported threshold alert. Does not constitute definitive proof of financial fraud.",
                })

            # 2. Cross-category multi-vector threats from phone_number_summary
            cur = conn.execute(
                """
                SELECT phone_e164, country_code, report_count, categories
                FROM phone_number_summary
                WHERE array_length(categories, 1) >= 3
                """
            )
            for row in cur.fetchall() or []:
                phone_e164, country_code, report_count, categories = row
                cats = list(categories) if categories else []
                event_id = _make_event_id("XCAT", phone_e164)
                signals.append({
                    "event_id": event_id,
                    "event_type": "cross_category_threat",
                    "priority": "HIGH",
                    "phone_e164": phone_e164,
                    "country_code": country_code,
                    "report_count": report_count,
                    "categories": cats,
                    "recent_reports_24h": 0,
                    "reason": f"Multi-vector scam pattern: reported across {len(cats)} distinct categories ({', '.join(sorted(cats))}).",
                    "evidence_source": "Multi-category community reports in phone_number_summary.",
                    "confidence_qualification": "Indicates diverse suspicious activity reported by users; not verified by banking audit.",
                })

            # 3. 24-hour reputation spike from phone_report_submissions
            cur = conn.execute(
                """
                SELECT s.phone_e164, s.country_code,
                       count(DISTINCT s.reporter_hash) AS recent_24h,
                       array_agg(DISTINCT c) AS spike_cats
                FROM phone_report_submissions s, unnest(s.categories) AS c
                WHERE s.submitted_at >= (now() - INTERVAL '24 hours')
                  AND s.reporter_hash IS NOT NULL
                GROUP BY s.phone_e164, s.country_code
                HAVING count(DISTINCT s.reporter_hash) >= 3
                """
            )
            for row in cur.fetchall() or []:
                phone_e164, country_code, recent_24h, spike_cats = row
                cats = list(spike_cats) if spike_cats else []
                event_id = _make_event_id("SPIKE", phone_e164)
                priority = "CRITICAL" if recent_24h >= 5 else "HIGH"
                signals.append({
                    "event_id": event_id,
                    "event_type": "reputation_spike",
                    "priority": priority,
                    "phone_e164": phone_e164,
                    "country_code": country_code,
                    "report_count": recent_24h,
                    "categories": cats,
                    "recent_reports_24h": recent_24h,
                    "reason": f"Rapid surge of {recent_24h} independent reports submitted in the last 24 hours.",
                    "evidence_source": "Time-windowed submissions in phone_report_submissions deduplicated by reporter hash.",
                    "confidence_qualification": "Active spike signal. Indicates high-velocity campaign; does not establish account compromise.",
                })

            # 4. Disputed threats from phone_number_disputes
            cur = conn.execute(
                """
                SELECT s.phone_e164, s.country_code, s.report_count, s.categories
                FROM phone_number_summary s
                INNER JOIN phone_number_disputes d ON s.phone_e164 = d.phone_e164
                WHERE d.review_status = 'pending'
                GROUP BY s.phone_e164, s.country_code, s.report_count, s.categories
                """
            )
            for row in cur.fetchall() or []:
                phone_e164, country_code, report_count, categories = row
                cats = list(categories) if categories else []
                event_id = _make_event_id("DISP", phone_e164)
                signals.append({
                    "event_id": event_id,
                    "event_type": "disputed_threat",
                    "priority": "MEDIUM",
                    "phone_e164": phone_e164,
                    "country_code": country_code,
                    "report_count": report_count,
                    "categories": cats,
                    "recent_reports_24h": 0,
                    "reason": f"Contested reputation: number has {report_count} community report(s) and a pending dispute under review.",
                    "evidence_source": "Correlated records from phone_number_summary and phone_number_disputes.",
                    "confidence_qualification": "Under active dispute. Do not apply automated blocking without human verification.",
                })

            # Upsert all identified signals into security_feed_events
            for sig in signals:
                conn.execute(
                    """
                    INSERT INTO security_feed_events
                        (event_id, event_type, priority, phone_e164, country_code,
                         report_count, categories, recent_reports_24h, reason,
                         evidence_source, confidence_qualification, review_status,
                         first_detected, last_updated)
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s, %s, %s, %s, 'new', now(), now())
                    ON CONFLICT (event_id) DO UPDATE SET
                        report_count            = EXCLUDED.report_count,
                        categories              = EXCLUDED.categories,
                        recent_reports_24h      = EXCLUDED.recent_reports_24h,
                        priority                = EXCLUDED.priority,
                        reason                  = EXCLUDED.reason,
                        evidence_source         = EXCLUDED.evidence_source,
                        confidence_qualification = EXCLUDED.confidence_qualification,
                        last_updated            = now()
                    """,
                    (
                        sig["event_id"],
                        sig["event_type"],
                        sig["priority"],
                        sig["phone_e164"],
                        sig["country_code"],
                        sig["report_count"],
                        sig["categories"],
                        sig["recent_reports_24h"],
                        sig["reason"],
                        sig["evidence_source"],
                        sig["confidence_qualification"],
                    ),
                )
            conn.commit()

        return len(signals)
    except Exception:
        raise RuntimeError(
            "The security feed database is temporarily unavailable."
        )


def get_security_feed(
    limit: int = 20,
    offset: int = 0,
    event_type: Optional[str] = None,
    priority: Optional[str] = None,
    review_status: Optional[str] = None,
    mask_phone: bool = False,
) -> Dict[str, Any]:
    """Retrieve paginated security operations feed events with optional filters."""
    safe_limit = max(1, min(limit, 100))
    safe_offset = max(0, offset)

    # Validate filters
    if event_type and event_type not in VALID_EVENT_TYPES:
        raise ValueError(
            f"Invalid event_type '{event_type}'. Allowed: {', '.join(sorted(VALID_EVENT_TYPES))}."
        )
    if priority and priority not in VALID_PRIORITIES:
        raise ValueError(
            f"Invalid priority '{priority}'. Allowed: {', '.join(sorted(VALID_PRIORITIES))}."
        )
    if review_status and review_status not in VALID_REVIEW_STATUSES:
        raise ValueError(
            f"Invalid review_status '{review_status}'. Allowed: {', '.join(sorted(VALID_REVIEW_STATUSES))}."
        )

    # Sync signals from existing tables first
    sync_security_feed_signals()

    conditions: List[str] = []
    params: List[Any] = []

    if event_type:
        conditions.append("event_type = %s")
        params.append(event_type)
    if priority:
        conditions.append("priority = %s")
        params.append(priority)
    if review_status:
        conditions.append("review_status = %s")
        params.append(review_status)

    where_clause = f"WHERE {' AND '.join(conditions)}" if conditions else ""

    count_sql = f"SELECT count(*) FROM security_feed_events {where_clause}"
    select_sql = f"""
        SELECT event_id, event_type, priority, phone_e164, country_code,
               report_count, categories, recent_reports_24h, reason,
               evidence_source, confidence_qualification, review_status,
               acknowledged_by, acknowledged_at, notes, first_detected, last_updated
        FROM security_feed_events
        {where_clause}
        ORDER BY
            CASE priority
                WHEN 'CRITICAL' THEN 1
                WHEN 'HIGH' THEN 2
                WHEN 'MEDIUM' THEN 3
                ELSE 4
            END,
            last_updated DESC
        LIMIT %s OFFSET %s
    """

    try:
        with get_connection() as conn:
            total = conn.execute(count_sql, tuple(params)).fetchone()[0]

            query_params = tuple(params + [safe_limit, safe_offset])
            rows = conn.execute(select_sql, query_params).fetchall() or []
    except Exception:
        raise RuntimeError(
            "The security feed database is temporarily unavailable."
        )

    items: List[Dict[str, Any]] = []
    for row in rows:
        (
            event_id,
            ev_type,
            ev_prio,
            phone_e164,
            country_code,
            report_count,
            categories,
            recent_24h,
            reason,
            ev_source,
            conf_qual,
            r_status,
            ack_by,
            ack_at,
            notes,
            first_det,
            last_upd,
        ) = row

        cats = list(categories) if categories else []
        ack_at_str = ack_at.isoformat() if hasattr(ack_at, "isoformat") else (str(ack_at) if ack_at else None)
        first_det_str = first_det.isoformat() if hasattr(first_det, "isoformat") else (str(first_det) if first_det else None)
        last_upd_str = last_upd.isoformat() if hasattr(last_upd, "isoformat") else (str(last_upd) if last_upd else None)

        display_phone = mask_phone_number(phone_e164) if mask_phone else phone_e164

        items.append({
            "event_id": event_id,
            "event_type": ev_type,
            "priority": ev_prio,
            "phone_number": display_phone,
            "masked_phone": mask_phone_number(phone_e164),
            "country_code": country_code,
            "report_count": report_count,
            "categories": cats,
            "recent_reports_24h": recent_24h,
            "reason": reason,
            "evidence_source": ev_source,
            "confidence_qualification": conf_qual,
            "review_status": r_status,
            "acknowledged_by": ack_by,
            "acknowledged_at": ack_at_str,
            "notes": notes,
            "first_detected": first_det_str,
            "last_updated": last_upd_str,
        })

    return {
        "total": total,
        "limit": safe_limit,
        "offset": safe_offset,
        "has_more": (safe_offset + len(items)) < total,
        "items": items,
    }


def get_security_feed_event(event_id: str, mask_phone: bool = False) -> Optional[Dict[str, Any]]:
    """Fetch details of a single security feed event by ID."""
    clean_id = event_id.strip() if event_id else ""
    if not clean_id:
        return None

    try:
        with get_connection() as conn:
            row = conn.execute(
                """
                SELECT event_id, event_type, priority, phone_e164, country_code,
                       report_count, categories, recent_reports_24h, reason,
                       evidence_source, confidence_qualification, review_status,
                       acknowledged_by, acknowledged_at, notes, first_detected, last_updated
                FROM security_feed_events
                WHERE event_id = %s
                """,
                (clean_id,),
            ).fetchone()
    except Exception:
        raise RuntimeError(
            "The security feed database is temporarily unavailable."
        )

    if row is None:
        return None

    (
        ev_id,
        ev_type,
        ev_prio,
        phone_e164,
        country_code,
        report_count,
        categories,
        recent_24h,
        reason,
        ev_source,
        conf_qual,
        r_status,
        ack_by,
        ack_at,
        notes,
        first_det,
        last_upd,
    ) = row

    cats = list(categories) if categories else []
    ack_at_str = ack_at.isoformat() if hasattr(ack_at, "isoformat") else (str(ack_at) if ack_at else None)
    first_det_str = first_det.isoformat() if hasattr(first_det, "isoformat") else (str(first_det) if first_det else None)
    last_upd_str = last_upd.isoformat() if hasattr(last_upd, "isoformat") else (str(last_upd) if last_upd else None)

    display_phone = mask_phone_number(phone_e164) if mask_phone else phone_e164

    return {
        "event_id": ev_id,
        "event_type": ev_type,
        "priority": ev_prio,
        "phone_number": display_phone,
        "masked_phone": mask_phone_number(phone_e164),
        "country_code": country_code,
        "report_count": report_count,
        "categories": cats,
        "recent_reports_24h": recent_24h,
        "reason": reason,
        "evidence_source": ev_source,
        "confidence_qualification": conf_qual,
        "review_status": r_status,
        "acknowledged_by": ack_by,
        "acknowledged_at": ack_at_str,
        "notes": notes,
        "first_detected": first_det_str,
        "last_updated": last_upd_str,
    }


def update_feed_event_status(
    event_id: str,
    new_status: str,
    analyst_id: str,
    notes: Optional[str] = None,
) -> Dict[str, Any]:
    """Acknowledge or update the review status of a security feed event."""
    clean_id = event_id.strip() if event_id else ""
    clean_status = new_status.strip().lower() if new_status else ""

    if clean_status not in VALID_REVIEW_STATUSES:
        raise ValueError(
            f"Invalid review_status '{new_status}'. Allowed: {', '.join(sorted(VALID_REVIEW_STATUSES))}."
        )

    clean_notes = notes.strip()[:500] if notes and str(notes).strip() else None

    try:
        with get_connection() as conn:
            cur = conn.execute(
                """
                UPDATE security_feed_events SET
                    review_status   = %s,
                    acknowledged_by = %s,
                    acknowledged_at = now(),
                    notes           = COALESCE(%s, notes),
                    last_updated    = now()
                WHERE event_id = %s
                RETURNING event_id
                """,
                (clean_status, analyst_id.strip(), clean_notes, clean_id),
            )
            updated = cur.fetchone()
            if updated is None:
                raise KeyError(f"Event '{event_id}' not found.")
            conn.commit()

        return get_security_feed_event(clean_id)  # type: ignore
    except KeyError:
        raise
    except ValueError:
        raise
    except Exception:
        raise RuntimeError(
            "The security feed database is temporarily unavailable."
        )
