import React from "react";
import { Camera, Cpu } from "lucide-react";
import { useLiveClock } from "../../hooks/useLiveClock";
import { useInspection } from "../../context/InspectionContext";

export default function Header({ title, subtitle }) {
  const now = useLiveClock();
  const { cameraStatus, aiStatus } = useInspection();

  const dateStr = now.toLocaleDateString("fr-FR", { day: "2-digit", month: "short", year: "numeric" });
  const timeStr = now.toLocaleTimeString("fr-FR", { hour12: false });

  return (
    <header className="h-16 shrink-0 flex items-center justify-between px-8 border-b border-border bg-surface/80 backdrop-blur-sm sticky top-0 z-10">
      <div>
        <h1 className="text-[15px] font-semibold leading-none">{title}</h1>
        {subtitle && <p className="text-xs text-muted mt-1">{subtitle}</p>}
      </div>

      <div className="flex items-center gap-6 text-xs text-muted">
        <div className="flex items-center gap-1.5">
          <Camera size={14} strokeWidth={1.75} />
          <span className={cameraStatus?.connected ? "text-success" : "text-error"}>
            {cameraStatus?.connected ? "Caméra connectée" : "Caméra hors ligne"}
          </span>
        </div>
        <div className="flex items-center gap-1.5">
          <Cpu size={14} strokeWidth={1.75} />
          <span className={aiStatus?.available ? "text-success" : "text-error"}>
            {aiStatus ? `IA ${aiStatus.mode}` : "IA —"}
          </span>
        </div>
        <div className="font-mono-num">{dateStr} · {timeStr}</div>
      </div>
    </header>
  );
}
