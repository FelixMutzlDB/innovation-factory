"""Main router for vi-home-one project, mounting all sub-routers."""
from fastapi import APIRouter

from .routers import (
    neighborhoods,
    households,
    energy,
    optimization,
    providers,
    maintenance,
    tickets,
    chat,
)

router = APIRouter(tags=["vi-home-one"])

router.include_router(neighborhoods.router)
router.include_router(households.router)
router.include_router(energy.router)
router.include_router(optimization.router)
router.include_router(providers.router)
router.include_router(maintenance.router)
router.include_router(tickets.router)
router.include_router(chat.router)
