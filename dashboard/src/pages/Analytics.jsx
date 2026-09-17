import React from "react";
import Header from "../components/layout/Header";
import StatCard from "../components/analytics/StatCard";
import ConfidenceTrendChart from "../components/analytics/ConfidenceTrendChart";
import DurationTrendChart from "../components/analytics/DurationTrendChart";
import { useStats, useHistory } from "../hooks/useInspectionData";

export default function Analytics() {
  const { stats, loading: statsLoading } = useStats();
  const { history, loading: historyLoading } = useHistory();

  if (statsLoading || !stats) {
    return (
      <>
        <Header title="Analytics" subtitle="Performance du contrôle de conformité" />
        <div className="p-8 text-sm text-muted">Chargement des statistiques…</div>
      </>
    );
  }

  return (
    <>
      <Header title="Analytics" subtitle="Performance du contrôle de conformité" />
      <div className="p-8 flex flex-col gap-6">
        <div className="grid grid-cols-2 lg:grid-cols-4 gap-6">
          <StatCard value={stats.total.toLocaleString("fr-FR")} label="Inspections totales" />
          <StatCard value={`${stats.success_rate}%`} label="Taux de réussite" tone="success" />
          <StatCard value={stats.failed} label="Non conformes" tone="error" />
          <StatCard value={`${(stats.avg_duration_ms / 1000).toFixed(1)}s`} label="Durée moyenne" />
        </div>
        {!historyLoading && (
          <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
            <ConfidenceTrendChart history={history} />
            <DurationTrendChart history={history} />
          </div>
        )}
        <p className="text-xs text-muted">
          Historique en mémoire côté backend (repart de zéro à chaque redémarrage du serveur).
        </p>
      </div>
    </>
  );
}
