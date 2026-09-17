from fastapi import APIRouter, Depends

from app.api.dependencies import get_inspection_service
from app.schemas.inspection import InspectionHistoryEntry, InspectionRequest, InspectionResult, InspectionStats
from app.services.inspection_service import InspectionService

router = APIRouter(prefix="/inspection", tags=["inspection"])


@router.post("/run", response_model=InspectionResult)
async def run_inspection(
    request: InspectionRequest | None = None,
    inspection_service: InspectionService = Depends(get_inspection_service),
):
    return await inspection_service.run(request)


@router.get("/history", response_model=list[InspectionHistoryEntry])
async def inspection_history(
    limit: int = 50,
    inspection_service: InspectionService = Depends(get_inspection_service),
):
    return inspection_service.get_history(limit=limit)


@router.get("/stats", response_model=InspectionStats)
async def inspection_stats(
    inspection_service: InspectionService = Depends(get_inspection_service),
):
    return inspection_service.get_stats()
