from fastapi import Request

from app.services.ai_service import AIServiceWrapper
from app.services.camera_service import CameraService
from app.services.inspection_service import InspectionService


def get_camera_service(request: Request) -> CameraService:
    return request.app.state.camera_service


def get_ai_service(request: Request) -> AIServiceWrapper:
    return request.app.state.ai_service


def get_inspection_service(request: Request) -> InspectionService:
    return request.app.state.inspection_service
