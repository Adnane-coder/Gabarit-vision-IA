from fastapi import APIRouter, Request

from app.schemas.system import SystemInfo

router = APIRouter(prefix="/system", tags=["system"])


@router.get("/info", response_model=SystemInfo)
async def system_info(request: Request):
    settings = request.app.state.settings
    return SystemInfo(
        app_name=settings.APP_NAME,
        environment=settings.ENVIRONMENT,
        mock_mode=settings.MOCK_MODE,
        camera_enabled=settings.CAMERA_ENABLED,
        ai_enabled=settings.AI_ENABLED,
    )
