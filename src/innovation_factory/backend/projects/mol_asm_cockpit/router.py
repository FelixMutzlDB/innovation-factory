"""Main router for mol-asm-cockpit project, mounting all sub-routers."""
from fastapi import APIRouter

from .routers import stations, sales, anomalies, inventory, workforce, chat, dashboard

router = APIRouter(tags=["mol-asm-cockpit"])

router.include_router(stations.router)
router.include_router(sales.router)
router.include_router(anomalies.router)
router.include_router(inventory.router)
router.include_router(workforce.router)
router.include_router(chat.router)
router.include_router(dashboard.router)
