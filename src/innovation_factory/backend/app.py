from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.responses import JSONResponse
from fastapi.staticfiles import StaticFiles
from slowapi.errors import RateLimitExceeded
from slowapi.middleware import SlowAPIMiddleware

from .._metadata import app_name, dist_dir
from .config import AppConfig
from .rate_limit import limiter
from .router import api
from .runtime import Runtime
from .utils import add_not_found_handler
from .logger import logger


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Initialize config and runtime, store in app.state for dependency injection
    config = AppConfig()
    logger.info(f"Starting app with configuration:\n{config}")

    runtime = Runtime(config)
    runtime.validate_db()
    runtime.initialize_models()

    # Auto-seed if database is empty (works in dev and production)
    from .seed import check_and_seed_if_empty
    try:
        check_and_seed_if_empty(runtime)
    except Exception as e:
        logger.warning(f"Seeding skipped (likely concurrent worker race): {e}")

    # Store in app.state for access via dependencies
    app.state.config = config
    app.state.runtime = runtime

    yield


app = FastAPI(title=f"{app_name}", lifespan=lifespan)
ui = StaticFiles(directory=dist_dir, html=True)


# --- Rate limiting (slowapi) -------------------------------------------------
# The limiter is defined in rate_limit.py and keys requests on the
# authenticated user (X-Forwarded-User) with IP fallback for local dev.
# Per-endpoint budgets are set on individual route handlers via the
# @limiter.limit("N/minute") decorator — see routers/ideas.py and each
# project's chat router for examples.
app.state.limiter = limiter
app.add_middleware(SlowAPIMiddleware)  # type: ignore[invalid-argument-type]  # starlette's Protocol is narrower than slowapi's middleware class


@app.exception_handler(RateLimitExceeded)
async def _rate_limit_exceeded(request: Request, exc: RateLimitExceeded) -> JSONResponse:
    """Return a JSON error body for 429s.

    Civion-safe lesson 19.11: the default Starlette exception handler
    for RateLimitExceeded returns plain text; our frontend JSON parser
    would choke. We set ``media_type="application/json"`` explicitly
    and include a ``Retry-After`` header so clients can back off.
    """
    retry_after = getattr(exc, "retry_after", None) or 60
    return JSONResponse(
        status_code=429,
        content={
            "error": "rate_limit_exceeded",
            "detail": f"Rate limit exceeded: {exc.detail}",
            "retry_after_seconds": retry_after,
        },
        headers={"Retry-After": str(retry_after)},
    )


# note the order of includes and mounts!
app.include_router(api)
app.mount("/", ui)


add_not_found_handler(app)
