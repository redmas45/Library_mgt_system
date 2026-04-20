"""
Auth middleware — optional global authentication enforcement.

Note: Primary auth is handled via dependency injection in routes.
This middleware provides an additional layer for global protection
of specific paths if needed.
"""

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse


class AuthMiddleware(BaseHTTPMiddleware):
    """
    Global auth middleware for path-level protection.

    By default, this is a pass-through. Enable protection
    for specific paths by adding them to PROTECTED_PREFIXES.
    """

    # Paths that require auth at the middleware level (optional)
    PROTECTED_PREFIXES = []

    # Paths that are always public
    PUBLIC_PATHS = [
        "/health",
        "/docs",
        "/redoc",
        "/openapi.json",
        "/api/auth/login",
        "/api/auth/register",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        # Skip public paths
        if any(path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)

        # Check protected prefixes (if any are configured)
        if self.PROTECTED_PREFIXES:
            if any(path.startswith(p) for p in self.PROTECTED_PREFIXES):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(
                        status_code=401,
                        content={"detail": "Authentication required"},
                    )

        return await call_next(request)
