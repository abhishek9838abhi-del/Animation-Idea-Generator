"""FastAPI Application Entry Point for Frame by Frame."""

import logging
from pathlib import Path
from fastapi import FastAPI, Request, Response, status
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse, FileResponse
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.limiter import rate_limiter, get_client_ip, RateLimitExceeded
from app.schemas import (
    AnimationPlan,
    GenerateRequest,
    ReviseRequest,
    ErrorResponse,
    ErrorDetail,
)
from app.provider import (
    provider_adapter,
    ProviderError,
    ProviderNotConfiguredError,
    ProviderTimeoutError,
    ProviderAPIError,
    ProviderJSONParseError,
)

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s [%(levelname)s] %(name)s: %(message)s",
)
logger = logging.getLogger("frame_by_frame")

app = FastAPI(
    title=settings.app_name,
    version="1.0.0",
    description="Backend API for Frame by Frame: Animation Idea Generator",
)

# CORS configuration
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# ---------------------------------------------------------------------------
# Global Exception Handlers (Safe responses, zero secret or stack leaks)
# ---------------------------------------------------------------------------
@app.exception_handler(RateLimitExceeded)
async def rate_limit_handler(request: Request, exc: RateLimitExceeded):
    return JSONResponse(
        status_code=status.HTTP_429_TOO_MANY_REQUESTS,
        headers={"Retry-After": str(exc.retry_after)},
        content={
            "error": {
                "code": "RATE_LIMIT_EXCEEDED",
                "message": f"Too many requests. Please wait {exc.retry_after} seconds before trying again.",
                "details": {"retry_after": exc.retry_after},
            }
        },
    )


@app.exception_handler(RequestValidationError)
async def validation_exception_handler(request: Request, exc: RequestValidationError):
    first_error = exc.errors()[0] if exc.errors() else {}
    msg = first_error.get("msg", "Invalid request body.")
    loc = " -> ".join(str(l) for l in first_error.get("loc", []))
    safe_details = [
        {
            "loc": [str(x) for x in err.get("loc", [])],
            "msg": err.get("msg", ""),
            "type": err.get("type", ""),
        }
        for err in exc.errors()
    ]
    return JSONResponse(
        status_code=status.HTTP_422_UNPROCESSABLE_ENTITY,
        content={
            "error": {
                "code": "SCHEMA_VALIDATION_ERROR",
                "message": f"Validation failed at '{loc}': {msg}",
                "details": safe_details,
            }
        },
    )


@app.exception_handler(ProviderNotConfiguredError)
async def provider_not_configured_handler(request: Request, exc: ProviderNotConfiguredError):
    return JSONResponse(
        status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": "Set the NVIDIA_API_KEY environment variable to enable live generation.",
            }
        },
    )


@app.exception_handler(ProviderTimeoutError)
async def provider_timeout_handler(request: Request, exc: ProviderTimeoutError):
    return JSONResponse(
        status_code=status.HTTP_504_GATEWAY_TIMEOUT,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": None,
            }
        },
    )


@app.exception_handler(ProviderAPIError)
async def provider_api_error_handler(request: Request, exc: ProviderAPIError):
    return JSONResponse(
        status_code=exc.status_code,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": None,
            }
        },
    )


@app.exception_handler(ProviderJSONParseError)
async def provider_parse_error_handler(request: Request, exc: ProviderJSONParseError):
    return JSONResponse(
        status_code=status.HTTP_502_BAD_GATEWAY,
        content={
            "error": {
                "code": exc.code,
                "message": exc.message,
                "details": None,
            }
        },
    )


@app.exception_handler(Exception)
async def generic_exception_handler(request: Request, exc: Exception):
    logger.exception("Unhandled server exception: %s", str(exc))
    return JSONResponse(
        status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
        content={
            "error": {
                "code": "INTERNAL_SERVER_ERROR",
                "message": "An unexpected error occurred. Please try again later.",
                "details": None,
            }
        },
    )


# ---------------------------------------------------------------------------
# API Routes
# ---------------------------------------------------------------------------
@app.get("/api/health")
async def health_check():
    """Returns service health and provider configuration state."""
    return {
        "status": "ok",
        "service": settings.app_name,
        "version": "1.0.0",
        "provider": {
            "name": "nvidia",
            "configured": provider_adapter.is_configured,
            "model": settings.nvidia_model,
        },
    }


@app.post("/api/generate", response_model=AnimationPlan)
async def generate_plan(request: Request, body: GenerateRequest, response: Response):
    """Generates an animation plan from a creative idea prompt."""
    ip = get_client_ip(request)
    allowed, remaining, retry_after = rate_limiter.check(ip)
    if not allowed:
        raise RateLimitExceeded(retry_after=retry_after)

    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    logger.info("Plan generation requested by %s for runtime=%s", ip, body.runtime.value)
    return await provider_adapter.generate_plan(body)


@app.post("/api/revise", response_model=AnimationPlan)
async def revise_plan(request: Request, body: ReviseRequest, response: Response):
    """Revises an existing animation plan based on user delta instructions."""
    ip = get_client_ip(request)
    allowed, remaining, retry_after = rate_limiter.check(ip)
    if not allowed:
        raise RateLimitExceeded(retry_after=retry_after)

    response.headers["X-RateLimit-Limit"] = str(settings.rate_limit_per_minute)
    response.headers["X-RateLimit-Remaining"] = str(remaining)

    logger.info("Plan revision requested by %s", ip)
    return await provider_adapter.revise_plan(body)


# ---------------------------------------------------------------------------
# Static Web Files Mount
# ---------------------------------------------------------------------------
static_dir = Path(__file__).resolve().parent.parent / "static"
if static_dir.exists():
    app.mount("/static", StaticFiles(directory=str(static_dir)), name="static")

    @app.get("/")
    async def serve_index():
        return FileResponse(static_dir / "index.html")
