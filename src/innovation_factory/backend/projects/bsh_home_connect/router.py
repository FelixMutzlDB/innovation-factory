"""Main router for bsh-home-connect project, mounting all sub-routers."""
from fastapi import APIRouter

from .routers import users, devices, tickets, chat, knowledge

router = APIRouter(tags=["bsh-home-connect"])

router.include_router(users.router)
router.include_router(devices.router)
router.include_router(tickets.router)
router.include_router(chat.router)
router.include_router(knowledge.router)
