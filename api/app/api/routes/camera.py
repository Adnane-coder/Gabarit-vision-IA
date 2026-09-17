from fastapi import APIRouter, Depends

from app.api.dependencies import get_camera_service
from app.schemas.camera import CameraCaptureResponse, CameraStatus
from app.services.camera_service import CameraService

router = APIRouter(prefix="/camera", tags=["camera"])


@router.get("/status", response_model=CameraStatus)
async def camera_status(camera_service: CameraService = Depends(get_camera_service)):
    status = await camera_service.get_status()
    return CameraStatus(**status)


@router.post("/capture", response_model=CameraCaptureResponse)
async def camera_capture(camera_service: CameraService = Depends(get_camera_service)):
    result = await camera_service.capture()
    return CameraCaptureResponse(success=True, **result)
