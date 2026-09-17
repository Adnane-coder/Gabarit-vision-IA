from abc import ABC, abstractmethod
from typing import Any, Dict

from app.core.exceptions import InferenceError
from app.core.logging import get_logger

logger = get_logger(__name__)


class AIService(ABC):
    """Contract any inspection model backend must satisfy."""

    @abstractmethod
    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]: ...

    @abstractmethod
    def is_available(self) -> bool: ...


class RealAIService(AIService):
    """Runs the real conformity pipeline (app/models/conformity_pipeline.py),
    ported from notebooks/10_pipeline_conformite.ipynb: PDF -> U-Net
    segmentation -> measurement -> greedy matching against the reference
    table -> per-piece verdict.

    Unlike a live camera frame, this pipeline works on a known tracé PDF
    (Tracee1-4) — `context` must contain a `tracee` key. This is a
    deliberate adaptation of the AIService contract to match how the real
    system actually works today; a future camera-fed capture step would
    populate `context["tracee"]` after identifying the model/tracé, rather
    than passing a raw camera frame directly to this service.
    """

    def __init__(self, model_manager):
        self.model_manager = model_manager

    def is_available(self) -> bool:
        return self.model_manager.has_any_checkpoint()

    async def analyze(self, context: Dict[str, Any]) -> Dict[str, Any]:
        from app.models.conformity_pipeline import verifier_conformite_tracee

        tracee = context.get("tracee")
        if not tracee:
            raise InferenceError(
                "RealAIService requires a 'tracee' identifier (e.g. 'Tracee1') "
                "— the real pipeline works on known tracé PDFs, not arbitrary camera frames."
            )

        settings = self.model_manager.settings
        try:
            resultat = verifier_conformite_tracee(
                tracee,
                checkpoints_dir=settings.CHECKPOINTS_DIR,
                reference_table_path=settings.REFERENCE_TABLE_PATH,
                trace_pdf_dir=settings.TRACEES_PDF_DIR,
                annotations_dir=settings.ANNOTATIONS_DIR,
                results_dir=settings.RESULTS_DIR,
                tolerance_cm=settings.TOLERANCE_CM,
                min_area_cm2=settings.MIN_AREA_CM2,
                device=self.model_manager.device,
            )
        except (FileNotFoundError, KeyError) as exc:
            raise InferenceError(str(exc)) from exc

        taux = resultat["taux_conformite_global"] or 0.0
        return {
            "result": "PASS" if resultat["n_non_conformes"] == 0 and resultat["n_manquantes"] == 0 else "FAIL",
            "confidence": round(taux, 4),
            "defects": [
                {
                    "type": piece["verdict"].lower().replace(" ", "_"),
                    "description": _describe_piece(piece),
                    "severity": "high" if piece["verdict"] in ("NON CONFORME", "MANQUANTE") else "low",
                }
                for piece in resultat["rapport_detaille"]
                if piece["verdict"] != "CONFORME"
            ],
            "pipeline_result": resultat,
        }


def _describe_piece(piece: Dict[str, Any]) -> str:
    if piece["verdict"] == "NON CONFORME":
        return (
            f"{piece['piece_reference']}: mesure "
            f"{piece['largeur_mesuree_cm']}x{piece['hauteur_mesuree_cm']}cm vs attendu "
            f"{piece['largeur_attendue_cm']}x{piece['hauteur_attendue_cm']}cm "
            f"(ecart {piece['erreur_cm']}cm)"
        )
    if piece["verdict"] == "MANQUANTE":
        return f"{piece['piece_reference']}: piece de reference non detectee"
    return "Detection sans correspondance dans la reference"
