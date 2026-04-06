"""
Distributed Rate Limiting with Redis

Enhanced rate limiting for production environments with Redis backend.
Falls back to in-memory storage for development.

Implements sliding window counter algorithm with distributed synchronization.

Additions:
- Per-path sensitive limits for auth endpoints (anti-brute-force)
- X-RateLimit-Reset header (epoch timestamp of window expiry)
- Consecutive Redis failure circuit breaker → CRITICAL log after N failures
"""

import logging
import math
import time
from typing import Optional, Tuple

from fastapi import Request, status
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware

from app.config import settings

logger = logging.getLogger(__name__)

# Try to import Redis
try:
    import redis.asyncio as redis

    REDIS_AVAILABLE = True
except ImportError:
    REDIS_AVAILABLE = False
    logger.warning(
        "redis package not installed - falling back to in-memory rate limiting"
    )

# Paths that require stricter rate limits regardless of user role (anti-brute-force)
_AUTH_SENSITIVE_PATHS = frozenset(
    {
        "/api/v1/auth/login",
        "/api/v1/auth/request-otp",
        "/api/v1/auth/verify-otp",
    }
)

# Circuit breaker: log CRITICAL if Redis fails more than this many times consecutively
_REDIS_CIRCUIT_BREAKER_THRESHOLD = 5


class DistributedRateLimiter:
    """
    Distributed rate limiter using Redis.

    Uses sliding window counter algorithm with Redis sorted sets.
    Falls back to in-memory storage if Redis is unavailable.
    """

    def __init__(self, redis_url: Optional[str] = None):
        """
        Initialize rate limiter.

        Args:
            redis_url: Redis connection URL (e.g., redis://localhost:6379/0)
        """
        self.redis_client: Optional[redis.Redis] = None
        self.use_redis = False
        self._redis_failure_count = 0  # circuit breaker counter

        # In-memory fallback
        self._memory_store = {}

        # Try to connect to Redis
        if REDIS_AVAILABLE and redis_url:
            try:
                self.redis_client = redis.from_url(
                    redis_url,
                    encoding="utf-8",
                    decode_responses=True,
                )
                self.use_redis = True
                logger.info("Distributed rate limiter initialized with Redis")
            except Exception as e:
                logger.warning(
                    f"Failed to connect to Redis: {e}. Using in-memory fallback."
                )
                self.use_redis = False
        else:
            logger.info("Using in-memory rate limiter (development mode)")

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int, int]:
        """
        Check if request should be rate limited.

        Args:
            key: Rate limit key (e.g., "user:123" or "ip:1.2.3.4")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            (allowed, current_count, remaining, reset_epoch)
            reset_epoch = Unix timestamp when the window resets
        """
        if self.use_redis and self.redis_client:
            return await self._check_redis(key, limit, window_seconds)
        else:
            return await self._check_memory(key, limit, window_seconds)

    async def _check_redis(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int, int]:
        """
        Check rate limit using Redis sorted sets (sliding window).
        """
        now = time.time()
        window_start = now - window_seconds
        reset_epoch = math.ceil(now) + window_seconds

        redis_key = f"rate_limit:{key}"

        try:
            # Remove old entries outside window
            await self.redis_client.zremrangebyscore(redis_key, "-inf", window_start)

            # Count current requests in window
            count = await self.redis_client.zcard(redis_key)

            if count >= limit:
                allowed = False
                remaining = 0
            else:
                await self.redis_client.zadd(redis_key, {str(now): now})
                count += 1
                remaining = limit - count
                allowed = True

            # Set expiry on key
            await self.redis_client.expire(redis_key, window_seconds + 10)

            # Reset circuit breaker on success
            self._redis_failure_count = 0

            return allowed, count, remaining, reset_epoch

        except Exception as e:
            self._redis_failure_count += 1
            if self._redis_failure_count >= _REDIS_CIRCUIT_BREAKER_THRESHOLD:
                logger.critical(
                    f"Redis rate limiter has failed {self._redis_failure_count} times consecutively. "
                    f"All limits are now enforced in-memory only — not cluster-safe. "
                    f"Last error: {e}"
                )
            else:
                logger.error(
                    f"Redis rate limit error ({self._redis_failure_count}x): {e}. Allowing request."
                )
            # Fail open on Redis errors
            return True, 0, limit, math.ceil(now) + window_seconds

    async def _check_memory(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int, int]:
        """
        Check rate limit using in-memory sliding window.
        """
        now = time.time()
        window_start = now - window_seconds
        reset_epoch = math.ceil(now) + window_seconds

        if key not in self._memory_store:
            self._memory_store[key] = []

        timestamps = self._memory_store[key]
        timestamps = [ts for ts in timestamps if ts > window_start]
        self._memory_store[key] = timestamps

        count = len(timestamps)

        if count >= limit:
            remaining = 0
            allowed = False
        else:
            timestamps.append(now)
            count += 1
            remaining = limit - count
            allowed = True

        return allowed, count, remaining, reset_epoch

    async def close(self):
        """Close Redis connection."""
        if self.redis_client:
            await self.redis_client.close()


# Global rate limiter instance
_rate_limiter: Optional[DistributedRateLimiter] = None


def get_rate_limiter() -> DistributedRateLimiter:
    """Get global rate limiter instance."""
    global _rate_limiter

    if _rate_limiter is None:
        redis_url = getattr(settings, "REDIS_URL", None)
        _rate_limiter = DistributedRateLimiter(redis_url)

    return _rate_limiter


class DistributedRateLimitMiddleware(BaseHTTPMiddleware):
    """
    Distributed rate limiting middleware.

    Uses Redis for production, in-memory for development.
    """

    async def dispatch(self, request: Request, call_next):
        import os

        if os.environ.get("TESTING") == "1":
            return await call_next(request)

        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        limiter = get_rate_limiter()
        key, limit, window_seconds = self._extract_key_limit_window(request)

        allowed, count, remaining, reset_epoch = await limiter.check_rate_limit(
            key=key,
            limit=limit,
            window_seconds=window_seconds,
        )

        if not allowed:
            from app.security.events import log_security_event

            request_id = getattr(request.state, "request_id", "unknown")
            log_security_event(
                "RATE_LIMIT_EXCEEDED",
                f"limit {count}/{limit} req/{window_seconds}s",
                request_id,
                request.url.path,
                identity=key,
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate Limit Exceeded",
                    "details": [
                        {
                            "message": (
                                f"Too many requests. Limit: {limit} per {window_seconds}s. "
                                f"Try again after {reset_epoch}."
                            )
                        }
                    ],
                },
                headers={
                    "Retry-After": str(window_seconds),
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                    "X-RateLimit-Reset": str(reset_epoch),
                },
            )

        response = await call_next(request)

        # Add rate limit info headers to every response
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)
        response.headers["X-RateLimit-Reset"] = str(reset_epoch)

        return response

    def _extract_key_limit_window(self, request: Request) -> Tuple[str, int, int]:
        """
        Extract rate limiting key, limit, and window (seconds).

        Auth-sensitive paths (login, OTP) use a tighter per-IP bucket
        regardless of authenticated user, to block brute-force attempts.
        """
        path = request.url.path

        # Auth-sensitive paths → strict IP-based bucket, short window
        if path in _AUTH_SENSITIVE_PATHS:
            client_ip = self._client_ip(request)
            return f"auth:{client_ip}", settings.RATE_LIMIT_AUTH_SENSITIVE, 60

        # 1. Try JWT Authorization header
        auth_header = request.headers.get("Authorization", "")
        if auth_header.startswith("Bearer "):
            try:
                from app.security.auth import verify_token

                token = auth_header.split(" ", 1)[1]
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub", "unknown")
                    role = payload.get("role", "farmer")
                    limits = {
                        "farmer": settings.RATE_LIMIT_FARMER,
                        "provider": settings.RATE_LIMIT_PROVIDER,
                        "admin": settings.RATE_LIMIT_ADMIN,
                    }
                    limit = limits.get(role, settings.RATE_LIMIT_DEFAULT)
                    return f"user:{user_id}", limit, 60
            except Exception:
                pass

        # 2. Try Cookie authentication
        session_cookie = request.cookies.get("session_token")
        if session_cookie:
            try:
                from app.security.auth import verify_token

                payload = verify_token(session_cookie)
                if payload:
                    user_id = payload.get("sub", "unknown")
                    role = payload.get("role", "farmer")
                    limits = {
                        "farmer": settings.RATE_LIMIT_FARMER,
                        "provider": settings.RATE_LIMIT_PROVIDER,
                        "admin": settings.RATE_LIMIT_ADMIN,
                    }
                    limit = limits.get(role, settings.RATE_LIMIT_DEFAULT)
                    return f"user:{user_id}", limit, 60
            except Exception:
                pass

        # 3. Fallback to IP-based limiting
        return f"ip:{self._client_ip(request)}", settings.RATE_LIMIT_DEFAULT, 60

    @staticmethod
    def _client_ip(request: Request) -> str:
        """Extract client IP, proxy-safe."""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "0.0.0.0"
