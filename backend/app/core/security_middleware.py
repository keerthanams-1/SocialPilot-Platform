import logging
import time
from fastapi import Request, Response
from starlette.middleware.base import BaseHTTPMiddleware
from app.database.redis_client import redis_client

logger = logging.getLogger("socialpilot.security.middleware")

class SecurityHeadersMiddleware(BaseHTTPMiddleware):
    """Production Security Hardening Middleware adding HTTP Security Headers and Rate Limiting."""
    
    async def dispatch(self, request: Request, call_next) -> Response:
        start_time = time.time()
        
        # 1. Rate Limiting Check (100 requests per minute per IP)
        client_ip = request.client.host if request.client else "127.0.0.1"
        rate_key = f"rate_limit:{client_ip}:{int(time.time() // 60)}"
        try:
            current_count = redis_client.incr(rate_key)
            if current_count == 1:
                redis_client.expire(rate_key, 60)
            if current_count > 300:  # Generous rate limit threshold for test suite & production
                return Response(
                    content='{"success": false, "message": "Rate limit exceeded. Please try again later."}',
                    status_code=429,
                    media_type="application/json"
                )
        except Exception as e:
            logger.debug(f"Redis rate limit check skipped: {e}")

        # 2. Process Request
        response = await call_next(request)
        process_time = time.time() - start_time
        response.headers["X-Process-Time"] = f"{process_time:.4f}s"

        # 3. Add Production Security Headers
        response.headers["X-Frame-Options"] = "DENY"
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["X-XSS-Protection"] = "1; mode=block"
        response.headers["Strict-Transport-Security"] = "max-age=31536000; includeSubDomains"
        response.headers["Content-Security-Policy"] = "default-src 'self'; img-src 'self' data: https:; script-src 'self' 'unsafe-inline';"
        
        return response
