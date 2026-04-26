"""
Simple in-memory rate limiter for API endpoints.
"""

import time
from typing import Dict, Tuple
from collections import defaultdict
import threading


class RateLimiter:
    """Thread-safe in-memory rate limiter."""

    def __init__(self):
        self._requests: Dict[str, list] = defaultdict(list)
        self._lock = threading.Lock()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> bool:
        """Check if request is allowed based on rate limit."""
        now = time.time()
        window_start = now - window_seconds

        with self._lock:
            # Clean old requests
            self._requests[key] = [t for t in self._requests[key] if t > window_start]

            if len(self._requests[key]) >= max_requests:
                return False

            self._requests[key].append(now)
            return True

    def reset(self, key: str):
        """Reset rate limit for a specific key."""
        with self._lock:
            if key in self._requests:
                del self._requests[key]


# Global rate limiter instance
rate_limiter = RateLimiter()


def check_rate_limit(key: str, max_requests: int = 100, window_seconds: int = 60) -> bool:
    """Check if request is allowed. Returns True if allowed, False if rate limited."""
    return rate_limiter.is_allowed(key, max_requests, window_seconds)