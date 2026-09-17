import random
from typing import Any, Dict

from app.models.inference import AIService


class MockAIService(AIService):
    """Simulates model inference with realistic, slightly varying results
    so the frontend has something dynamic to render while real inference
    isn't wired up yet."""

    def is_available(self) -> bool:
        return True

    async def analyze(self, image: Dict[str, Any]) -> Dict[str, Any]:
        passed = random.random() > 0.08  # ~92% pass rate, close to project's real numbers
        confidence = round(random.uniform(0.93, 0.99) if passed else random.uniform(0.55, 0.8), 3)

        defects = []
        if not passed:
            defects.append(
                {
                    "type": "dimension_mismatch",
                    "description": "Measured piece dimension exceeds the ±3cm tolerance.",
                    "severity": "high",
                }
            )

        return {
            "result": "PASS" if passed else "FAIL",
            "confidence": confidence,
            "defects": defects,
        }
