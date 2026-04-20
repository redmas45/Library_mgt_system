"""
Rate limiter middleware using slowapi.
"""

from slowapi import Limiter, _rate_limit_exceeded_handler
from slowapi.util import get_remote_address
from slowapi.errors import RateLimitExceeded
from fastapi import FastAPI

from app.config import get_settings

settings = get_settings()

# Create limiter instance
limiter = Limiter(
    key_func=get_remote_address,
    default_limits=[settings.RATE_LIMIT],
)


def setup_rate_limiter(app: FastAPI):
    """Configure rate limiting on the FastAPI app."""
    app.state.limiter = limiter
    app.add_exception_handler(RateLimitExceeded, _rate_limit_exceeded_handler)
