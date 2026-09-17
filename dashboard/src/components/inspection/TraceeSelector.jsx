import React, { useState } from "react";
import { ScanLine, Loader2 } from "lucide-react";
import { motion } from "framer-motion";
import Card from "../ui/Card";
import { TRACEES } from "../../services/inspectionService";
import { useInspection } from "../../context/InspectionContext";

export default function TraceeSelector() {
  const [tracee, setTracee] = useState(TRACEES[0]);
  const { launchInspection, running, cameraStatus, aiStatus } = useInspection();

  const canRun = cameraStatus?.connected && aiStatus?.available && !running;

  return (
    <Card className="flex flex-col gap-4">
      <div className="text-xs text-muted">Contrôle de conformité</div>

      <div>
        <label className="text-xs text-muted block mb-1.5">Tracé à analyser</label>
        <select
          value={tracee}
          onChange={(e) => setTracee(e.target.value)}
          disabled={running}
          className="w-full bg-sunken border border-border rounded-md px-3 py-2.5 text-sm outline-none focus:border-accent"
        >
          {TRACEES.map((t) => (
            <option key={t} value={t}>{t}</option>
          ))}
        </select>
      </div>

      <button
        onClick={() => launchInspection(tracee)}
        disabled={!canRun}
        className="flex items-center justify-center gap-2 bg-accent text-white rounded-md py-2.5 text-sm font-medium transition-opacity disabled:opacity-40 hover:opacity-90"
      >
        {running ? (
          <motion.span animate={{ rotate: 360 }} transition={{ repeat: Infinity, duration: 1, ease: "linear" }}>
            <Loader2 size={16} />
          </motion.span>
        ) : (
          <ScanLine size={16} strokeWidth={1.75} />
        )}
        {running ? "Analyse en cours…" : "Lancer l'inspection"}
      </button>

      {!cameraStatus?.connected && (
        <p className="text-xs text-error">Caméra indisponible — impossible de lancer une inspection.</p>
      )}
      {cameraStatus?.connected && !aiStatus?.available && (
        <p className="text-xs text-error">Modèle IA indisponible.</p>
      )}
    </Card>
  );
}
