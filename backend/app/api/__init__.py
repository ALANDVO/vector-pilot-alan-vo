from fastapi import APIRouter

from .v1 import evaluations, health

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(evaluations.router)