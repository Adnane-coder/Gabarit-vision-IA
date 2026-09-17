from functools import lru_cache
from typing import List

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    """Central configuration. Values are read from environment variables /
    a .env file — never hardcode these elsewhere in the codebase."""

    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")

    APP_NAME: str = "AI Inspection Platform"
    ENVIRONMENT: str = "development"
    API_V1_PREFIX: str = "/api/v1"

    # Global switch: true while camera + AI are not physically available.
    MOCK_MODE: bool = True

    CAMERA_ENABLED: bool = False
    CAMERA_DEVICE: str = "raspberry_pi"

    AI_ENABLED: bool = False
    MODEL_PATH: str = "./models"

    # Real conformity pipeline (ported from notebooks/10_pipeline_conformite.ipynb).
    # Defaults assume `api/` sits next to `models/` and `data/` at the project root
    # (gabarit-vision-ia/), matching the notebooks' own relative paths one level up.
    CHECKPOINTS_DIR: str = "../models/saved"
    REFERENCE_TABLE_PATH: str = "../data/processed/reference_dimensions.json"
    TRACEES_PDF_DIR: str = "../data/raw/reference"
    ANNOTATIONS_DIR: str = "../data/processed"
    RESULTS_DIR: str = "../data/results"
    TOLERANCE_CM: float = 3.0
    MIN_AREA_CM2: float = 10.0

    LOG_LEVEL: str = "INFO"

    # Comma-separated in .env, e.g. "http://localhost:3000,http://localhost:5173"
    CORS_ORIGINS: str = "http://localhost:3000,http://localhost:5173"

    @property
    def cors_origins_list(self) -> List[str]:
        return [origin.strip() for origin in self.CORS_ORIGINS.split(",") if origin.strip()]


@lru_cache
def get_settings() -> Settings:
    # Cached so Settings() is only parsed once per process.
    return Settings()
