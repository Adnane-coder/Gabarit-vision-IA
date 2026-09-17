from typing import Any, Dict

from app.core.exceptions import CameraCaptureError, CameraUnavailableError
from app.core.logging import get_logger
from app.hardware.camera import CameraInterface

logger = get_logger(__name__)


class CameraService:
    def __init__(self, camera: CameraInterface):
        self.camera = camera

    async def get_status(self) -> Dict[str, Any]:
        try:
            return await self.camera.get_status()
        except NotImplementedError as exc:
            raise CameraUnavailableError(str(exc)) from exc

    async def capture(self) -> Dict[str, Any]:
        try:
            logger.info("Capturing image...")
            result = await self.camera.capture()
            logger.info("Image captured: %s", result.get("image_id"))
            return result
        except NotImplementedError as exc:
            raise CameraUnavailableError(str(exc)) from exc
        except Exception as exc:  # pragma: no cover - defensive
            raise CameraCaptureError(str(exc)) from exc
