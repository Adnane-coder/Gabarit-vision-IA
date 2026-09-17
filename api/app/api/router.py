from fastapi import APIRouter

from app.api.routes import ai, camera, health, inspection, system

api_router = APIRouter()
api_router.include_router(health.router)
api_router.include_router(system.router)
api_router.include_router(camera.router)
api_router.include_router(ai.router)
api_router.include_router(inspection.router)
