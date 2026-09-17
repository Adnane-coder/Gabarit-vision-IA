from typing import Any, Dict

from app.core.exceptions import InferenceError, ModelUnavailableError
from app.core.logging import get_logger
from app.models.inference import AIService as AIServiceInterface

logger = get_logger(__name__)


class AIServiceWrapper:
    def __init__(self, ai_service: AIServiceInterface, model_name: str, mock_mode: bool):
        self.ai_service = ai_service
        self.model_name = model_name
        self.mock_mode = mock_mode

    def get_status(self) -> Dict[str, Any]:
        return {
            "available": self.ai_service.is_available(),
            "mode": "mock" if self.mock_mode else "real",
            "model_loaded": self.ai_service.is_available() and not self.mock_mode,
            "model_name": self.model_name,
        }

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        if not self.ai_service.is_available():
            raise ModelUnavailableError()
        try:
            logger.info("Running inference...")
            result = await self.ai_service.analyze(context)
            logger.info("Inference completed: %s", result.get("result"))
            return result
        except NotImplementedError as exc:
            raise ModelUnavailableError(str(exc)) from exc
        except InferenceError:
            raise
        except Exception as exc:  # pragma: no cover - defensive
            raise InferenceError(str(exc)) from exc
