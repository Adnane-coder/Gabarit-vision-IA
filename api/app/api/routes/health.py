from fastapi import APIRouter, Request

from app.schemas.system import HealthResponse

router = APIRouter(tags=["health"])


@router.get("/health", response_model=HealthResponse)
async def health(request: Request):
    settings = request.app.state.settings
    return HealthResponse(
        status="ok",
        backend="online",
        mode="mock" if settings.MOCK_MODE else "real",
    )
