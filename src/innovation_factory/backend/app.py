from contextlib import asynccontextmanager

from fastapi import FastAPI
from fastapi.staticfiles import StaticFiles

from .._metadata import app_name, dist_dir
from .config import AppConfig
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

# note the order of includes and mounts!
app.include_router(api)
app.mount("/", ui)


add_not_found_handler(app)
