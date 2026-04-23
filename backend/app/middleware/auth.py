from starlette.middleware.base import BaseHTTPMiddleware
from starlette.requests import Request
from starlette.responses import JSONResponse

class AuthMiddleware(BaseHTTPMiddleware):
    PROTECTED_PREFIXES = []
    PUBLIC_PATHS = [
        "/health", "/docs", "/redoc", "/openapi.json",
        "/api/auth/login", "/api/auth/register",
    ]

    async def dispatch(self, request: Request, call_next):
        path = request.url.path

        if any(path.startswith(p) for p in self.PUBLIC_PATHS):
            return await call_next(request)

        if self.PROTECTED_PREFIXES:
            if any(path.startswith(p) for p in self.PROTECTED_PREFIXES):
                auth_header = request.headers.get("Authorization")
                if not auth_header or not auth_header.startswith("Bearer "):
                    return JSONResponse(status_code=401, content={"detail": "Authentication required"})

        return await call_next(request)
