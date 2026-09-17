import uuid
from datetime import datetime, timezone
from typing import Any, Dict

from app.hardware.camera import CameraInterface


class MockCamera(CameraInterface):
    """Simulates a connected camera with realistic, stable values so the
    frontend can be built and tested end-to-end before real hardware exists."""

    def __init__(self):
        self._connected = False

    async def connect(self) -> None:
        self._connected = True

    async def disconnect(self) -> None:
        self._connected = False

    async def capture(self) -> Dict[str, Any]:
        return {
            "image_id": f"IMG-{uuid.uuid4().hex[:10]}",
            "captured_at": datetime.now(timezone.utc),
            "resolution": "1920x1080",
        }

    async def get_status(self) -> Dict[str, Any]:
        return {
            "connected": True,
            "active": True,
            "device": "Mock Camera",
            "resolution": "1920x1080",
            "fps": 30,
        }
