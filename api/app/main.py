from contextlib import asynccontextmanager

from fastapi import FastAPI, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse

from app.api.router import api_router
from app.core.config import get_settings
from app.core.exceptions import AppError
from app.core.logging import get_logger, setup_logging
from app.hardware.raspberry_pi import RaspberryPiCamera
from app.mocks.ai_mock import MockAIService
from app.mocks.camera_mock import MockCamera
from app.models.inference import RealAIService
from app.models.model_manager import ModelManager
from app.services.ai_service import AIServiceWrapper
from app.services.camera_service import CameraService
from app.services.inspection_service import InspectionService

setup_logging()
logger = get_logger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    settings = get_settings()
    app.state.settings = settings

    # --- Camera: swap MockCamera for RaspberryPiCamera once hardware exists ---
    camera_backend = RaspberryPiCamera(settings.CAMERA_DEVICE) if settings.CAMERA_ENABLED else MockCamera()
    camera_service = CameraService(camera_backend)
    if isinstance(camera_backend, MockCamera):
        await camera_backend.connect()

    # --- AI: swap MockAIService for RealAIService once model artifacts exist ---
    model_manager = ModelManager(settings)
    model_manager.load()
    ai_backend = RealAIService(model_manager) if settings.AI_ENABLED else MockAIService()
    ai_service = AIServiceWrapper(ai_backend, model_name="inspection-model", mock_mode=settings.MOCK_MODE)

    inspection_service = InspectionService(camera_service, ai_service)

    app.state.camera_service = camera_service
    app.state.ai_service = ai_service
    app.state.inspection_service = inspection_service
    app.state.model_manager = model_manager

    logger.info("Backend started (mode=%s)", "mock" if settings.MOCK_MODE else "real")
    logger.info("Camera service initialized (%s)", type(camera_backend).__name__)
    logger.info("AI service initialized (%s)", type(ai_backend).__name__)

    yield

    logger.info("Backend shutting down")


def create_app() -> FastAPI:
    settings = get_settings()
    app = FastAPI(title=settings.APP_NAME, lifespan=lifespan)

    app.add_middleware(
        CORSMiddleware,
        allow_origins=settings.cors_origins_list,
        allow_credentials=True,
        allow_methods=["*"],
        allow_headers=["*"],
    )

    @app.exception_handler(AppError)
    async def app_error_handler(request: Request, exc: AppError):
        return JSONResponse(
            status_code=exc.status_code,
            content={"success": False, "error": {"code": exc.code, "message": exc.message}},
        )

    app.include_router(api_router, prefix=settings.API_V1_PREFIX)

    return app


app = create_app()
