"""
Distributed Rate Limiting with Redis

Enhanced rate limiting for production environments with Redis backend.
Falls back to in-memory storage for development.

Implements sliding window counter algorithm with distributed synchronization.
"""

import logging
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
    logger.warning("redis package not installed - falling back to in-memory rate limiting")


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
                logger.warning(f"Failed to connect to Redis: {e}. Using in-memory fallback.")
                self.use_redis = False
        else:
            logger.info("Using in-memory rate limiter (development mode)")

    async def check_rate_limit(
        self,
        key: str,
        limit: int,
        window_seconds: int = 60,
    ) -> Tuple[bool, int, int]:
        """
        Check if request should be rate limited.

        Args:
            key: Rate limit key (e.g., "user:123" or "ip:1.2.3.4")
            limit: Maximum requests allowed in window
            window_seconds: Time window in seconds

        Returns:
            (allowed, current_count, remaining)
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
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using Redis sorted sets.

        Uses sliding window algorithm:
        - Store timestamps in sorted set
        - Remove old timestamps outside window
        - Count remaining timestamps
        """
        now = time.time()
        window_start = now - window_seconds

        redis_key = f"rate_limit:{key}"

        try:
            # Remove old entries outside window
            await self.redis_client.zremrangebyscore(
                redis_key,
                "-inf",
                window_start,
            )

            # Count current requests in window
            count = await self.redis_client.zcard(redis_key)

            if count >= limit:
                # Rate limit exceeded
                remaining = 0
                allowed = False
            else:
                # Add current request
                await self.redis_client.zadd(
                    redis_key,
                    {str(now): now},
                )
                count += 1
                remaining = limit - count
                allowed = True

            # Set expiry on key
            await self.redis_client.expire(redis_key, window_seconds + 10)

            return allowed, count, remaining

        except Exception as e:
            logger.error(f"Redis rate limit error: {e}. Allowing request.")
            # On error, allow request (fail open)
            return True, 0, limit

    async def _check_memory(
        self,
        key: str,
        limit: int,
        window_seconds: int,
    ) -> Tuple[bool, int, int]:
        """
        Check rate limit using in-memory storage.

        Simple sliding window implementation.
        """
        now = time.time()
        window_start = now - window_seconds

        # Get or create entry
        if key not in self._memory_store:
            self._memory_store[key] = []

        # Remove old timestamps
        timestamps = self._memory_store[key]
        timestamps = [ts for ts in timestamps if ts > window_start]
        self._memory_store[key] = timestamps

        count = len(timestamps)

        if count >= limit:
            # Rate limit exceeded
            remaining = 0
            allowed = False
        else:
            # Add current request
            timestamps.append(now)
            count += 1
            remaining = limit - count
            allowed = True

        return allowed, count, remaining

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
        # Skip rate limiting for health checks and docs
        if request.url.path in ("/health", "/", "/docs", "/redoc", "/openapi.json"):
            return await call_next(request)

        # Get rate limiter
        limiter = get_rate_limiter()

        # Determine rate limiting key and limit
        key, limit = self._extract_key_and_limit(request)

        # Check rate limit
        allowed, count, remaining = await limiter.check_rate_limit(
            key=key,
            limit=limit,
            window_seconds=60,
        )

        if not allowed:
            logger.warning(
                f"Rate limit exceeded for key={key} ({count}/{limit} req/min)"
            )
            return JSONResponse(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                content={
                    "success": False,
                    "error": "Rate Limit Exceeded",
                    "details": [{
                        "message": f"Too many requests. Limit: {limit}/min. Try again in 60s."
                    }],
                },
                headers={
                    "Retry-After": "60",
                    "X-RateLimit-Limit": str(limit),
                    "X-RateLimit-Remaining": "0",
                },
            )

        response = await call_next(request)

        # Add rate limit headers
        response.headers["X-RateLimit-Limit"] = str(limit)
        response.headers["X-RateLimit-Remaining"] = str(remaining)

        return response

    def _extract_key_and_limit(self, request: Request) -> Tuple[str, int]:
        """
        Extract rate limiting key and limit.

        Uses JWT if available, otherwise IP address.
        """
        auth_header = request.headers.get("Authorization", "")

        if auth_header.startswith("Bearer "):
            try:
                from app.security.auth import verify_token

                token = auth_header.split(" ", 1)[1]
                payload = verify_token(token)
                if payload:
                    user_id = payload.get("sub", "unknown")
                    role = payload.get("role", "farmer")

                    # Role-based limits
                    limits = {
                        "farmer": settings.RATE_LIMIT_FARMER,
                        "provider": settings.RATE_LIMIT_PROVIDER,
                        "admin": settings.RATE_LIMIT_ADMIN,
                    }
                    limit = limits.get(role, settings.RATE_LIMIT_DEFAULT)

                    return f"user:{user_id}", limit
            except Exception:
                pass

        # Fallback to IP-based limiting
        client_ip = request.client.host if request.client else "0.0.0.0"
        return f"ip:{client_ip}", settings.RATE_LIMIT_DEFAULT
