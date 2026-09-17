import React from "react";
import Header from "../components/layout/Header";
import Card from "../components/ui/Card";
import Badge from "../components/ui/Badge";
import { useHistory } from "../hooks/useInspectionData";

export default function History() {
  const { history, loading } = useHistory();

  return (
    <>
      <Header title="Historique" subtitle="Inspections de conformité récentes" />
      <div className="p-8">
        <Card padded={false} className="overflow-hidden">
          <table className="w-full text-sm">
            <thead>
              <tr className="text-left text-xs text-muted border-b border-border">
                <th className="px-5 py-3 font-medium">ID</th>
                <th className="px-5 py-3 font-medium">Horodatage</th>
                <th className="px-5 py-3 font-medium">Tracé</th>
                <th className="px-5 py-3 font-medium">Résultat</th>
                <th className="px-5 py-3 font-medium">Taux conformité</th>
                <th className="px-5 py-3 font-medium">Durée</th>
              </tr>
            </thead>
            <tbody>
              {!loading &&
                history.map((row) => (
                  <tr key={row.inspection_id} className="border-b border-border last:border-0 hover:bg-sunken/50 transition-colors">
                    <td className="px-5 py-3 font-mono-num text-muted">{row.inspection_id}</td>
                    <td className="px-5 py-3 font-mono-num">
                      {new Date(row.timestamp).toLocaleTimeString("fr-FR")}
                    </td>
                    <td className="px-5 py-3">{row.tracee}</td>
                    <td className="px-5 py-3">
                      {row.result === "PASS" ? (
                        <Badge variant="success" dot>Conforme</Badge>
                      ) : (
                        <Badge variant="error" dot>Non conforme</Badge>
                      )}
                    </td>
                    <td className="px-5 py-3 font-mono-num">{(row.confidence * 100).toFixed(1)}%</td>
                    <td className="px-5 py-3 font-mono-num">{(row.processing_time_ms / 1000).toFixed(1)}s</td>
                  </tr>
                ))}
            </tbody>
          </table>
        </Card>
        <p className="text-xs text-muted mt-4">
          Historique en mémoire côté backend (repart de zéro à chaque redémarrage du serveur).
        </p>
      </div>
    </>
  );
}
