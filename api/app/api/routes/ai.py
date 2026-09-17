from fastapi import APIRouter, Depends

from app.api.dependencies import get_ai_service
from app.schemas.ai import AIStatus
from app.services.ai_service import AIServiceWrapper

router = APIRouter(prefix="/ai", tags=["ai"])


@router.get("/status", response_model=AIStatus)
async def ai_status(ai_service: AIServiceWrapper = Depends(get_ai_service)):
    return AIStatus(**ai_service.get_status())
