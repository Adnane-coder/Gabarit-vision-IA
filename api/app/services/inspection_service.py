import time
import uuid
from datetime import datetime, timezone
from typing import List, Optional

from app.core.logging import get_logger
from app.schemas.inspection import (
    Defect,
    InspectionHistoryEntry,
    InspectionRequest,
    InspectionResult,
    InspectionStats,
    PieceVerdict,
)
from app.services.ai_service import AIServiceWrapper
from app.services.camera_service import CameraService

logger = get_logger(__name__)

MAX_HISTORY = 200


class InspectionService:
    def __init__(self, camera_service: CameraService, ai_service: AIServiceWrapper):
        self.camera_service = camera_service
        self.ai_service = ai_service
        # In-memory history — intentionally simple (no DB): resets on restart.
        # Good enough for a dev/demo dashboard; swap for real persistence
        # (e.g. SQLite) only if the project actually needs it to survive
        # restarts.
        self._history: List[InspectionResult] = []

    async def run(self, request: Optional[InspectionRequest] = None) -> InspectionResult:
        started_at = time.perf_counter()
        inspection_id = f"INS-2026-{uuid.uuid4().hex[:6].upper()}"
        logger.info("Inspection %s started", inspection_id)

        image = await self.camera_service.capture()
        logger.info("Image captured for inspection %s", inspection_id)

        context = dict(image)
        if request and request.tracee:
            context["tracee"] = request.tracee

        analysis = await self.ai_service.analyze(context)
        logger.info("Inspection %s result: %s", inspection_id, analysis["result"])

        elapsed_ms = int((time.perf_counter() - started_at) * 1000)
        pipeline_result = analysis.get("pipeline_result")

        result = InspectionResult(
            inspection_id=inspection_id,
            status="completed",
            result=analysis["result"],
            confidence=analysis["confidence"],
            defects=[Defect(**d) for d in analysis.get("defects", [])],
            processing_time_ms=elapsed_ms,
            created_at=datetime.now(timezone.utc).isoformat(),
            tracee=pipeline_result["tracee"] if pipeline_result else None,
            code_modele=pipeline_result["code_modele"] if pipeline_result else None,
            n_pieces_reference=pipeline_result["n_pieces_reference"] if pipeline_result else None,
            n_conformes=pipeline_result["n_conformes"] if pipeline_result else None,
            n_non_conformes=pipeline_result["n_non_conformes"] if pipeline_result else None,
            n_manquantes=pipeline_result["n_manquantes"] if pipeline_result else None,
            n_inattendues=pipeline_result["n_inattendues"] if pipeline_result else None,
            taux_conformite_global=pipeline_result["taux_conformite_global"] if pipeline_result else None,
            pieces=(
                [PieceVerdict(**p) for p in pipeline_result["rapport_detaille"]]
                if pipeline_result else None
            ),
        )

        self._history.append(result)
        if len(self._history) > MAX_HISTORY:
            self._history.pop(0)

        return result

    def get_history(self, limit: int = 50) -> List[InspectionHistoryEntry]:
        recent = list(reversed(self._history[-limit:]))
        return [
            InspectionHistoryEntry(
                inspection_id=r.inspection_id,
                timestamp=r.created_at,
                tracee=r.tracee,
                result=r.result,
                confidence=r.confidence,
                processing_time_ms=r.processing_time_ms,
            )
            for r in recent
        ]

    def get_stats(self) -> InspectionStats:
        if not self._history:
            return InspectionStats(total=0, passed=0, failed=0, success_rate=0.0, avg_duration_ms=0.0)

        total = len(self._history)
        passed = sum(1 for r in self._history if r.result == "PASS")
        failed = total - passed
        avg_duration_ms = sum(r.processing_time_ms for r in self._history) / total

        return InspectionStats(
            total=total,
            passed=passed,
            failed=failed,
            success_rate=round(passed / total * 100, 1),
            avg_duration_ms=round(avg_duration_ms, 1),
        )
