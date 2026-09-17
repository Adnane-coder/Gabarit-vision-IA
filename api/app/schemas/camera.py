from datetime import datetime

from pydantic import BaseModel


class CameraStatus(BaseModel):
    connected: bool
    active: bool
    device: str
    resolution: str
    fps: int


class CameraCaptureResponse(BaseModel):
    success: bool
    image_id: str
    captured_at: datetime
    resolution: str
