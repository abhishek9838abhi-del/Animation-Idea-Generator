"""In-memory Token Bucket / Sliding Window Rate Limiter for Frame by Frame."""

import time
from collections import defaultdict
from typing import Dict, List, Tuple
from fastapi import Request, HTTPException, status
from app.config import settings


class RateLimiter:
    """Sliding-window in-memory rate limiter per IP address."""

    def __init__(self, limit: int = 10, window_seconds: int = 60):
        self.limit = limit
        self.window_seconds = window_seconds
        self._history: Dict[str, List[float]] = defaultdict(list)

    def _clean_old_entries(self, key: str, now: float) -> None:
        threshold = now - self.window_seconds
        self._history[key] = [t for t in self._history[key] if t > threshold]

    def check(self, key: str) -> Tuple[bool, int, int]:
        """
        Checks if the request is permitted.
        Returns: (is_allowed, remaining_requests, retry_after_seconds)
        """
        now = time.time()
        self._clean_old_entries(key, now)

        history = self._history[key]
        if len(history) >= self.limit:
            oldest = history[0]
            retry_after = max(1, int(self.window_seconds - (now - oldest)))
            return False, 0, retry_after

        # Record this request timestamp
        history.append(now)
        remaining = self.limit - len(history)
        return True, remaining, 0

    def reset(self) -> None:
        """Clears the history (primarily for automated tests)."""
        self._history.clear()


rate_limiter = RateLimiter(
    limit=settings.rate_limit_per_minute, window_seconds=60
)


def get_client_ip(request: Request) -> str:
    """Safely extracts the client IP address from headers or connection."""
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    if request.client:
        return request.client.host
    return "127.0.0.1"


class RateLimitExceeded(HTTPException):
    def __init__(self, retry_after: int):
        super().__init__(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            detail=f"Rate limit exceeded. Please wait {retry_after} seconds.",
            headers={"Retry-After": str(retry_after)},
        )
        self.retry_after = retry_after
