"""
Rate limiting for API endpoints.

Uses an in-memory sliding window counter. Suitable for single-instance
deployments. For multi-instance, swap the storage to Redis.

Two usage patterns:
1. Middleware (global) — applies default limits to all requests
2. Dependency (per-route) — tighter limits on expensive endpoints

The middleware sets standard per-IP limits. Route-level dependencies
can add per-user limits on top for authenticated endpoints.

Rate limit headers returned:
- X-RateLimit-Limit: max requests in the window
- X-RateLimit-Remaining: requests remaining
- X-RateLimit-Reset: seconds until the window resets
"""

import time
from collections import defaultdict
from typing import Optional

from fastapi import HTTPException, Request, Response, status
from starlette.middleware.base import BaseHTTPMiddleware, RequestResponseEndpoint


class SlidingWindowCounter:
    """In-memory sliding window rate limiter.

    Stores timestamps of recent requests per key. On each check,
    prunes expired entries and counts remaining ones.

    Thread safety: FastAPI runs on asyncio (single thread per process),
    so no locks needed for the dict operations.
    """

    def __init__(self):
        # key -> list of request timestamps
        self._windows: dict[str, list[float]] = defaultdict(list)
        self._last_cleanup = time.monotonic()

    def is_allowed(self, key: str, max_requests: int, window_seconds: int) -> tuple[bool, int, int]:
        """Check if a request is allowed under the rate limit.

        Returns:
            (allowed, remaining, reset_seconds)
        """
        now = time.monotonic()

        # Periodic cleanup of stale keys (every 60s)
        if now - self._last_cleanup > 60:
            self._cleanup(now, window_seconds)

        # Prune expired timestamps for this key
        cutoff = now - window_seconds
        timestamps = self._windows[key]
        self._windows[key] = [t for t in timestamps if t > cutoff]
        timestamps = self._windows[key]

        remaining = max(0, max_requests - len(timestamps))
        reset_seconds = int(window_seconds - (now - timestamps[0])) if timestamps else window_seconds

        if len(timestamps) >= max_requests:
            return False, 0, reset_seconds

        # Allow and record
        self._windows[key].append(now)
        return True, remaining - 1, reset_seconds

    def _cleanup(self, now: float, default_window: int = 60):
        """Remove keys with all expired timestamps."""
        self._last_cleanup = now
        cutoff = now - default_window
        stale_keys = [k for k, v in self._windows.items() if all(t <= cutoff for t in v)]
        for k in stale_keys:
            del self._windows[k]


# Global singleton
_limiter = SlidingWindowCounter()


def _get_client_ip(request: Request) -> str:
    """Extract the real client IP, handling proxies."""
    # Check X-Forwarded-For first (common in production behind a proxy)
    forwarded = request.headers.get("x-forwarded-for")
    if forwarded:
        return forwarded.split(",")[0].strip()
    # Fall back to the direct client
    return request.client.host if request.client else "unknown"


class RateLimitMiddleware(BaseHTTPMiddleware):
    """Global rate limit middleware.

    Applies a generous per-IP limit to all requests. This catches
    abuse from unauthenticated scrapers/bots. Authenticated users
    get per-user limits from route dependencies for expensive ops.

    Default: 100 requests per minute per IP.
    """

    def __init__(self, app, requests_per_minute: int = 100):
        super().__init__(app)
        self.max_requests = requests_per_minute
        self.window_seconds = 60

    async def dispatch(
        self, request: Request, call_next: RequestResponseEndpoint
    ) -> Response:
        from app.config import settings

        # Skip rate limiting for health checks or when disabled (e.g. tests)
        if not settings.RATE_LIMIT_ENABLED or request.url.path in ("/", "/health"):
            return await call_next(request)

        client_ip = _get_client_ip(request)
        key = f"ip:{client_ip}"

        allowed, remaining, reset_seconds = _limiter.is_allowed(
            key, self.max_requests, self.window_seconds
        )

        if not allowed:
            return Response(
                content='{"detail":"Rate limit exceeded. Please try again later."}',
                status_code=429,
                media_type="application/json",
                headers={
                    "X-RateLimit-Limit": str(self.max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds),
                },
            )

        response = await call_next(request)

        # Add rate limit headers to successful responses
        response.headers["X-RateLimit-Limit"] = str(self.max_requests)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_seconds)

        return response


def rate_limit(max_requests: int = 10, window_seconds: int = 60):
    """Route-level rate limit dependency factory.

    Use this on expensive endpoints (creation of answers, evaluations,
    and AI generation) to add per-user limits on top of the global
    per-IP limit.

    Usage:
        @router.post("/endpoint", dependencies=[Depends(rate_limit(5, 60))])
        async def create_something(...):
            ...
    """

    async def _rate_limit_dep(request: Request) -> None:
        from app.config import settings

        if not settings.RATE_LIMIT_ENABLED:
            return

        # Try to get user ID from the request state (set by auth dependency)
        # Fall back to IP for unauthenticated requests
        user_id: Optional[str] = None
        if hasattr(request.state, "user_id"):
            user_id = request.state.user_id

        if user_id:
            key = f"user:{user_id}:{request.url.path}"
        else:
            client_ip = _get_client_ip(request)
            key = f"route:{client_ip}:{request.url.path}"

        allowed, remaining, reset_seconds = _limiter.is_allowed(
            key, max_requests, window_seconds
        )

        if not allowed:
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded. Max {max_requests} requests per {window_seconds}s. "
                f"Try again in {reset_seconds}s.",
                headers={
                    "X-RateLimit-Limit": str(max_requests),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_seconds),
                    "Retry-After": str(reset_seconds),
                },
            )

    return _rate_limit_dep
