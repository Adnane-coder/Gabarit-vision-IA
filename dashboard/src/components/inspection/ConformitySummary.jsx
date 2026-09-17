import React from "react";
import { CheckCircle2, AlertTriangle, Search } from "lucide-react";
import { motion, AnimatePresence } from "framer-motion";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import { useInspection } from "../../context/InspectionContext";

function Stat({ label, value, tone = "ink" }) {
  const toneClass = { ink: "text-ink", success: "text-success", error: "text-error", warning: "text-warning" }[tone];
  return (
    <div>
      <div className={`font-mono-num text-xl font-semibold ${toneClass}`}>{value}</div>
      <div className="text-[11px] text-muted mt-0.5">{label}</div>
    </div>
  );
}

export default function ConformitySummary() {
  const { lastResult, running } = useInspection();

  if (!lastResult && !running) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-10 text-muted">
        <Search size={28} strokeWidth={1.5} className="mb-3 opacity-50" />
        <p className="text-sm">Choisis un tracé et lance une inspection pour voir le verdict de conformité.</p>
      </Card>
    );
  }

  if (running) {
    return (
      <Card className="flex flex-col items-center justify-center text-center py-10 text-muted">
        <p className="text-sm">Segmentation U-Net en cours, mesure des pièces, comparaison à la référence…</p>
      </Card>
    );
  }

  const pass = lastResult.result === "PASS";
  // In mock mode the backend never runs the real pipeline (see MockAIService),
  // so per-piece detail and taux_conformite_global are null — only `confidence`
  // is populated. Show that distinction explicitly instead of rendering
  // misleading zeros/dashes as if it were a real, empty result.
  const isRealPipeline = lastResult.taux_conformite_global != null;
  const displayedRate = isRealPipeline ? lastResult.taux_conformite_global : lastResult.confidence;

  return (
    <Card className="flex flex-col gap-5">
      <AnimatePresence mode="wait">
        <motion.div
          key={lastResult.inspection_id}
          initial={{ opacity: 0, y: 4 }}
          animate={{ opacity: 1, y: 0 }}
          transition={{ duration: 0.25 }}
          className="flex items-start gap-3"
        >
          {pass ? (
            <CheckCircle2 size={28} className="text-success shrink-0" strokeWidth={1.75} />
          ) : (
            <AlertTriangle size={28} className="text-error shrink-0" strokeWidth={1.75} />
          )}
          <div className="flex-1">
            <div className="flex items-center gap-2">
              <span className={`text-base font-semibold ${pass ? "text-success" : "text-error"}`}>
                {pass ? "CONFORME" : "NON CONFORME"}
              </span>
              {!isRealPipeline && <Badge variant="neutral">mode mock</Badge>}
            </div>
            <p className="text-sm text-muted mt-0.5">
              {lastResult.tracee ?? "Aucun tracé (résultat simulé)"} {lastResult.code_modele ? `— modèle ${lastResult.code_modele}` : ""}
            </p>
          </div>
        </motion.div>
      </AnimatePresence>

      {!isRealPipeline && (
        <p className="text-xs text-muted -mt-2">
          Résultat simulé par le backend (AI_ENABLED=false) — le détail par pièce et le taux de
          conformité réel ne sont disponibles qu'en mode réel (AI_ENABLED=true).
        </p>
      )}

      <div className="grid grid-cols-2 gap-4 pt-4 border-t border-border">
        <Stat
          label={isRealPipeline ? "Taux de conformité" : "Confiance (simulée)"}
          value={`${(displayedRate * 100).toFixed(1)}%`}
          tone={pass ? "success" : "error"}
        />
        <Stat label="Temps de traitement" value={`${(lastResult.processing_time_ms / 1000).toFixed(2)}s`} />
        {isRealPipeline ? (
          <>
            <Stat label="Conformes" value={lastResult.n_conformes} tone="success" />
            <Stat label="Non conformes" value={lastResult.n_non_conformes} tone="error" />
            <Stat label="Manquantes" value={lastResult.n_manquantes} tone="warning" />
            <Stat label="Inattendues" value={lastResult.n_inattendues} />
          </>
        ) : (
          <div className="col-span-2 text-xs text-muted italic">
            Détail par pièce indisponible en mode mock.
          </div>
        )}
      </div>
    </Card>
  );
}
