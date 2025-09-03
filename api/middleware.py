from fastapi import Request, Response, HTTPException, status
from starlette.middleware.base import BaseHTTPMiddleware
from typing import Dict, Tuple, Callable, Optional, Union
import time
import asyncio
from pydantic import BaseModel, Field
import logging
from api.config import Settings

logger = logging.getLogger("middleware")

class RateLimitConfig(BaseModel):
    """Configuration for rate limiting"""
    enabled: bool = Field(default=False, description="Whether rate limiting is enabled")
    requests: int = Field(default=100, description="Maximum number of requests per time window")
    timespan: int = Field(default=60, description="Time window in seconds")
    block_duration: int = Field(default=300, description="Duration to block IP after limit exceeded (seconds)")

    # Optional whitelist of IPs that bypass rate limiting
    whitelist: list[str] = Field(default_factory=list, description="IPs that bypass rate limiting")


class TokenBucket:
    """Token bucket algorithm implementation for rate limiting"""

    def __init__(self, rate: float, capacity: int):
        self.rate = rate  # Tokens per second
        self.capacity = capacity  # Maximum tokens
        self.tokens = capacity  # Current token count
        self.last_refill = time.time()
        self.lock = asyncio.Lock()

    async def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket

        Args:
            tokens: Number of tokens to consume

        Returns:
            True if tokens were consumed, False otherwise
        """
        async with self.lock:
            # Refill tokens based on time elapsed
            now = time.time()
            elapsed = now - self.last_refill
            self.tokens = min(self.capacity, self.tokens + elapsed * self.rate)
            self.last_refill = now

            # Check if we have enough tokens
            if tokens <= self.tokens:
                self.tokens -= tokens
                return True
            return False


class RateLimitMiddleware(BaseHTTPMiddleware):
    """
    Middleware that implements rate limiting for API endpoints

    Features:
    - Token bucket algorithm for smooth rate limiting
    - Per-IP tracking to prevent abuse
    - Configurable rate limits
    - Whitelist for trusted IPs
    - Response headers showing rate limit status
    """

    def __init__(
        self,
        app,
        settings: Settings,
        get_client_id: Optional[Callable[[Request], str]] = None,
        excluded_paths: list[str] = None
    ):
        super().__init__(app)
        self.settings = settings
        self.enabled = settings.rate_limit_enabled
        self.requests_per_timespan = settings.rate_limit_requests
        self.timespan = settings.rate_limit_timespan

        # Function to get client identifier (defaults to IP address)
        self.get_client_id = get_client_id or self._get_client_ip

        # Paths that bypass rate limiting
        self.excluded_paths = excluded_paths or ["/docs", "/redoc", "/openapi.json", "/health"]

        # Token buckets per client
        self.buckets: Dict[str, TokenBucket] = {}

        # Blocked clients with unblock time
        self.blocked: Dict[str, float] = {}

        # IP whitelist
        self.whitelist = getattr(settings, "rate_limit_whitelist", [])

        # Token bucket settings
        self.rate = self.requests_per_timespan / self.timespan  # tokens per second
        self.capacity = min(self.requests_per_timespan, 20)  # max burst

        # Block duration in seconds
        self.block_duration = getattr(settings, "rate_limit_block_duration", 300)  # 5 minutes default

        # Cleanup task
        self._cleanup_task = asyncio.create_task(self._cleanup_loop())
        logger.info(f"Rate limiting {'enabled' if self.enabled else 'disabled'} with {self.requests_per_timespan} requests per {self.timespan} seconds")

    async def _cleanup_loop(self):
        """Periodically clean up stale buckets and blocked entries"""
        while True:
            try:
                await asyncio.sleep(60)  # Run every minute
                now = time.time()

                # Remove blocks that have expired
                self.blocked = {
                    client_id: unblock_time
                    for client_id, unblock_time in self.blocked.items()
                    if unblock_time > now
                }

                # Remove buckets for clients we haven't seen in a while (1 hour)
                cutoff = now - 3600
                stale_clients = []
                for client_id, bucket in self.buckets.items():
                    if bucket.last_refill < cutoff:
                        stale_clients.append(client_id)

                for client_id in stale_clients:
                    self.buckets.pop(client_id, None)

                if stale_clients:
                    logger.debug(f"Cleaned up {len(stale_clients)} stale rate limit buckets")

            except Exception as e:
                logger.error(f"Error in rate limit cleanup task: {e}")

    @staticmethod
    def _get_client_ip(request: Request) -> str:
        """Extract client IP from request, considering forwarded headers"""
        forwarded = request.headers.get("X-Forwarded-For")
        if forwarded:
            # Get the first IP in the chain
            return forwarded.split(",")[0].strip()
        return request.client.host if request.client else "unknown"

    def _get_bucket(self, client_id: str) -> TokenBucket:
        """Get or create a token bucket for the client"""
        if client_id not in self.buckets:
            self.buckets[client_id] = TokenBucket(self.rate, self.capacity)
        return self.buckets[client_id]

    async def dispatch(self, request: Request, call_next) -> Response:
        """Process the request through rate limiting"""
        # Skip if disabled or path is excluded
        if not self.enabled or any(request.url.path.startswith(path) for path in self.excluded_paths):
            return await call_next(request)

        # Get client identifier
        client_id = self.get_client_id(request)

        # Skip for whitelisted clients
        if client_id in self.whitelist:
            return await call_next(request)

        # Check if client is blocked
        now = time.time()
        if client_id in self.blocked:
            if self.blocked[client_id] > now:
                retry_after = int(self.blocked[client_id] - now)
                return self._rate_limited_response(retry_after)
            else:
                # Unblock if block duration has passed
                del self.blocked[client_id]

        # Get the client's token bucket
        bucket = self._get_bucket(client_id)

        # Try to consume a token
        if await bucket.consume(1):
            # Allow the request
            response = await call_next(request)

            # Add rate limit headers
            remaining = max(0, int(bucket.tokens))
            reset = int(now + (self.capacity - bucket.tokens) / self.rate)

            response.headers["X-RateLimit-Limit"] = str(self.requests_per_timespan)
            response.headers["X-RateLimit-Remaining"] = str(remaining)
            response.headers["X-RateLimit-Reset"] = str(reset)

            return response
        else:
            # Block the client
            self.blocked[client_id] = now + self.block_duration
            logger.warning(f"Rate limit exceeded for {client_id}. Blocked for {self.block_duration} seconds.")
            return self._rate_limited_response(self.block_duration)

    def _rate_limited_response(self, retry_after: int) -> Response:
        """Create a rate limited response"""
        from fastapi.responses import JSONResponse

        return JSONResponse(
            status_code=status.HTTP_429_TOO_MANY_REQUESTS,
            content={
                "status": "error",
                "code": 429,
                "message": "Too many requests. Please try again later.",
                "detail": f"Rate limit exceeded. Try again in {retry_after} seconds."
            },
            headers={
                "Retry-After": str(retry_after),
                "X-RateLimit-Limit": str(self.requests_per_timespan),
                "X-RateLimit-Remaining": "0",
                "X-RateLimit-Reset": str(int(time.time() + retry_after))
            }
        )
