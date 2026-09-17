from typing import Any, Dict

from app.hardware.camera import CameraInterface


class RaspberryPiCamera(CameraInterface):
    """Real camera backend for the Raspberry Pi deployment.

    Intentionally not implemented: the target hardware and camera module
    are not available yet, and this project's constraints say not to write
    against hardware we can't verify. Swapping MockCamera for this class in
    app/main.py (based on `settings.CAMERA_ENABLED`) is all that will be
    needed once the Pi + camera module are ready — no route or service
    code changes required.
    """

    def __init__(self, device: str = "raspberry_pi"):
        self.device = device

    async def connect(self) -> None:
        raise NotImplementedError("RaspberryPiCamera.connect: hardware not yet available.")

    async def disconnect(self) -> None:
        raise NotImplementedError("RaspberryPiCamera.disconnect: hardware not yet available.")

    async def capture(self) -> Dict[str, Any]:
        raise NotImplementedError("RaspberryPiCamera.capture: hardware not yet available.")

    async def get_status(self) -> Dict[str, Any]:
        raise NotImplementedError("RaspberryPiCamera.get_status: hardware not yet available.")
