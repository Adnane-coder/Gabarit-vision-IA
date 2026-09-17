// Mirrors the real backend's response shapes (see api/app/schemas/inspection.py,
// camera.py, ai.py) so switching VITE_API_BASE_URL on/off changes nothing
// else in the app.

export const KNOWN_TRACEES = ["Tracee1", "Tracee2", "Tracee3", "Tracee4"];

export function getMockCameraStatus() {
  return { connected: true, active: true, device: "Mock Camera", resolution: "1920x1080", fps: 30 };
}

export function getMockAiStatus() {
  return { available: true, mode: "mock", model_loaded: false, model_name: "inspection-model" };
}

const MOCK_PIECE_NAMES = [
  "FACING-04 CHAD-RIGHT", "CHAD-WB", "M0YA44-UNDERFLY", "PATCH", "CHAD-BACK",
  "M0YA44-FLY", "PASSANT", "M0YA44-LFRONT01", "YOKE CHAD-BACK", "CHAD-COIN PCKT-05",
];

export function getMockInspectionResult(tracee) {
  const nPieces = 20 + Math.floor(Math.random() * 15);
  const pieces = Array.from({ length: nPieces }, (_, i) => {
    const roll = Math.random();
    const nom = MOCK_PIECE_NAMES[i % MOCK_PIECE_NAMES.length];
    if (roll > 0.85) {
      return {
        piece_reference: nom, verdict: "NON CONFORME",
        largeur_attendue_cm: 20, hauteur_attendue_cm: 15,
        largeur_mesuree_cm: 24.5, hauteur_mesuree_cm: 15.2, erreur_cm: 4.5,
      };
    }
    if (roll > 0.93) {
      return { piece_reference: nom, verdict: "MANQUANTE" };
    }
    return {
      piece_reference: nom, verdict: "CONFORME",
      largeur_attendue_cm: 20, hauteur_attendue_cm: 15,
      largeur_mesuree_cm: 20.4, hauteur_mesuree_cm: 15.1, erreur_cm: 0.4,
    };
  });

  const n_conformes = pieces.filter((p) => p.verdict === "CONFORME").length;
  const n_non_conformes = pieces.filter((p) => p.verdict === "NON CONFORME").length;
  const n_manquantes = pieces.filter((p) => p.verdict === "MANQUANTE").length;
  const taux = n_conformes / pieces.length;

  return {
    inspection_id: `INS-2026-${Math.random().toString(16).slice(2, 8).toUpperCase()}`,
    status: "completed",
    result: n_non_conformes === 0 && n_manquantes === 0 ? "PASS" : "FAIL",
    confidence: Math.round(taux * 1000) / 1000,
    defects: pieces
      .filter((p) => p.verdict !== "CONFORME")
      .map((p) => ({
        type: p.verdict.toLowerCase().replace(" ", "_"),
        description: `${p.piece_reference}: ${p.verdict}`,
        severity: "high",
      })),
    processing_time_ms: 5000 + Math.floor(Math.random() * 3000),
    created_at: new Date().toISOString(),
    tracee,
    code_modele: "MOCK-MODEL",
    n_pieces_reference: pieces.length,
    n_conformes,
    n_non_conformes,
    n_manquantes,
    n_inattendues: 0,
    taux_conformite_global: Math.round(taux * 10000) / 10000,
    pieces,
  };
}

export function getMockStats() {
  return { total: 12, passed: 8, failed: 4, success_rate: 66.7, avg_duration_ms: 6200 };
}

export function getMockHistory() {
  return Array.from({ length: 8 }, (_, i) => ({
    inspection_id: `INS-2026-${(1000 - i).toString(16).toUpperCase()}`,
    timestamp: new Date(Date.now() - i * 1000 * 60 * 12).toISOString(),
    tracee: KNOWN_TRACEES[i % KNOWN_TRACEES.length],
    result: i % 3 === 0 ? "FAIL" : "PASS",
    confidence: i % 3 === 0 ? 0.71 : 0.96,
    processing_time_ms: 5000 + i * 200,
  }));
}
