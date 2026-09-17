from typing import List, Literal, Optional

from pydantic import BaseModel


class InspectionRequest(BaseModel):
    # Which known tracé to run conformity control against. Required in real
    # mode (the pipeline works on tracé PDFs, not arbitrary camera frames).
    # Ignored in mock mode.
    tracee: Optional[str] = None


class Defect(BaseModel):
    type: str
    description: str
    severity: Literal["low", "medium", "high"]


class PieceVerdict(BaseModel):
    piece_reference: Optional[str] = None
    largeur_attendue_cm: Optional[float] = None
    hauteur_attendue_cm: Optional[float] = None
    largeur_mesuree_cm: Optional[float] = None
    hauteur_mesuree_cm: Optional[float] = None
    erreur_cm: Optional[float] = None
    verdict: Literal["CONFORME", "NON CONFORME", "MANQUANTE", "INATTENDUE"]


class InspectionResult(BaseModel):
    inspection_id: str
    status: Literal["completed", "failed"]
    result: Literal["PASS", "FAIL"]
    confidence: float
    defects: List[Defect] = []
    processing_time_ms: int
    created_at: str

    # Present only in real mode: full per-piece conformity report.
    tracee: Optional[str] = None
    code_modele: Optional[str] = None
    n_pieces_reference: Optional[int] = None
    n_conformes: Optional[int] = None
    n_non_conformes: Optional[int] = None
    n_manquantes: Optional[int] = None
    n_inattendues: Optional[int] = None
    taux_conformite_global: Optional[float] = None
    pieces: Optional[List[PieceVerdict]] = None


class InspectionHistoryEntry(BaseModel):
    inspection_id: str
    timestamp: str
    tracee: Optional[str] = None
    result: Literal["PASS", "FAIL"]
    confidence: float
    processing_time_ms: int


class InspectionStats(BaseModel):
    total: int
    passed: int
    failed: int
    success_rate: float
    avg_duration_ms: float
