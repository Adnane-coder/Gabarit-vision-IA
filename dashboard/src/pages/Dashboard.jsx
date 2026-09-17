import React from "react";
import Header from "../components/layout/Header";
import TraceeSelector from "../components/inspection/TraceeSelector";
import ConformitySummary from "../components/inspection/ConformitySummary";
import StatCard from "../components/analytics/StatCard";
import { useStats } from "../hooks/useInspectionData";

export default function Dashboard() {
  const { stats } = useStats();

  return (
    <>
      <Header title="Vue d'ensemble" subtitle="Contrôle de conformité — SARTEX" />
      <div className="p-8 flex flex-col gap-6">
        <div className="grid grid-cols-1 lg:grid-cols-[320px_1fr] gap-6">
          <TraceeSelector />
          <ConformitySummary />
        </div>

        {stats && (
          <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
            <StatCard value={stats.total.toLocaleString("fr-FR")} label="Inspections totales" />
            <StatCard value={stats.passed.toLocaleString("fr-FR")} label="Conformes" tone="success" />
            <StatCard value={stats.failed} label="Non conformes" tone="error" />
            <StatCard value={`${stats.success_rate}%`} label="Taux de réussite" />
          </div>
        )}

        <p className="text-xs text-muted">
          Historique en mémoire côté backend (repart de zéro à chaque redémarrage du serveur).
        </p>
      </div>
    </>
  );
}
