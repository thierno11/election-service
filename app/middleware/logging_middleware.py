import time
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.services.logger import setup_logger

logger = setup_logger(__name__)


class RequestLoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        start_time = time.time()

        request_data = {
            "method": request.method,
            "url": str(request.url),
            "client_host": request.client.host if request.client else None,
            "user_agent": request.headers.get("user-agent"),
        }

        logger.info(f"Request started: {request.method} {request.url.path}", extra=request_data)

        response = await call_next(request)

        process_time = time.time() - start_time

        response_data = {
            **request_data,
            "status_code": response.status_code,
            "process_time": f"{process_time:.4f}s"
        }

        log_level = logger.error if response.status_code >= 400 else logger.info
        log_level(
            f"Request completed: {request.method} {request.url.path} - {response.status_code} ({process_time:.4f}s)",
            extra=response_data
        )

        response.headers["X-Process-Time"] = str(process_time)
        return response