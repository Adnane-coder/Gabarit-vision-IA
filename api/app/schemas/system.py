from pydantic import BaseModel


class HealthResponse(BaseModel):
    status: str
    backend: str
    mode: str


class SystemInfo(BaseModel):
    app_name: str
    environment: str
    mock_mode: bool
    camera_enabled: bool
    ai_enabled: bool
