# backend/app/rate_limiter.py
"""Thread-safe in-memory sliding-window rate limiter for public endpoints.

Protects critical write endpoints (such as community threat reporting) against
rapid-fire reputation poisoning, script automation, and denial-of-service attempts.
"""

from collections import deque
import os
import threading
import time
from typing import Deque, Dict, List, Tuple


class RateLimiter:
    """Sliding-window in-memory rate limiter per client IP."""

    def __init__(
        self,
        limits: List[Tuple[int, int]] | None = None,
    ) -> None:
        """Initialize the rate limiter.

        Parameters
        ----------
        limits:
            List of (max_requests, window_seconds) tuples.
            Defaults to:
              - 5 requests per 60 seconds (burst limit)
              - 25 requests per 3600 seconds (hourly limit)
        """
        if limits is None:
            limits = [(5, 60), (25, 3600)]
        self.limits = sorted(limits, key=lambda x: x[1])
        self.max_window = max(w for _, w in self.limits) if self.limits else 3600
        self._history: Dict[str, Deque[float]] = {}
        self._lock = threading.Lock()

    @property
    def is_enabled(self) -> bool:
        return os.environ.get("RATE_LIMITING_ENABLED", "true").lower() != "false"

    def check(self, client_ip: str) -> Tuple[bool, int]:
        """Check if *client_ip* is allowed to make a request.

        If allowed, records the request timestamp and returns (True, 0).
        If rate limited, returns (False, retry_after_seconds).
        """
        if not self.is_enabled:
            return True, 0

        now = time.monotonic()
        with self._lock:
            timestamps = self._history.setdefault(client_ip, deque())

            # Prune timestamps older than max window
            cutoff = now - self.max_window
            while timestamps and timestamps[0] < cutoff:
                timestamps.popleft()

            # Check all defined windows
            for max_reqs, window_sec in self.limits:
                window_cutoff = now - window_sec
                # Count timestamps within this window
                count = sum(1 for t in timestamps if t >= window_cutoff)
                if count >= max_reqs:
                    # Find earliest timestamp in this window
                    earliest = next(t for t in timestamps if t >= window_cutoff)
                    retry_after = int(window_sec - (now - earliest)) + 1
                    return False, max(retry_after, 1)

            # Record this valid request
            timestamps.append(now)
            return True, 0

    def reset(self) -> None:
        """Clear all rate limit history (used primarily between tests)."""
        with self._lock:
            self._history.clear()


report_rate_limiter = RateLimiter(limits=[(5, 60), (25, 3600)])
dispute_rate_limiter = RateLimiter(limits=[(5, 60), (20, 3600)])

