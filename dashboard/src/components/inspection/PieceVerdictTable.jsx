import React from "react";
import Card from "../ui/Card";
import Badge from "../ui/Badge";
import { useInspection } from "../../context/InspectionContext";

const VARIANT_BY_VERDICT = {
  CONFORME: "success",
  "NON CONFORME": "error",
  MANQUANTE: "warning",
  INATTENDUE: "neutral",
};

export default function PieceVerdictTable() {
  const { lastResult } = useInspection();

  if (!lastResult?.pieces?.length) return null;

  return (
    <Card padded={false} className="overflow-hidden">
      <div className="px-5 py-3 border-b border-border text-xs text-muted">
        Détail par pièce ({lastResult.pieces.length})
      </div>
      <div className="max-h-[420px] overflow-y-auto">
        <table className="w-full text-sm">
          <thead className="sticky top-0 bg-surface">
            <tr className="text-left text-xs text-muted border-b border-border">
              <th className="px-5 py-2.5 font-medium">Pièce</th>
              <th className="px-5 py-2.5 font-medium">Attendu (cm)</th>
              <th className="px-5 py-2.5 font-medium">Mesuré (cm)</th>
              <th className="px-5 py-2.5 font-medium">Écart</th>
              <th className="px-5 py-2.5 font-medium">Verdict</th>
            </tr>
          </thead>
          <tbody>
            {lastResult.pieces.map((p, i) => (
              <tr key={i} className="border-b border-border last:border-0 hover:bg-sunken/50">
                <td className="px-5 py-2.5">{p.piece_reference ?? <span className="text-muted italic">détection non référencée</span>}</td>
                <td className="px-5 py-2.5 font-mono-num text-muted">
                  {p.largeur_attendue_cm != null ? `${p.largeur_attendue_cm}×${p.hauteur_attendue_cm}` : "—"}
                </td>
                <td className="px-5 py-2.5 font-mono-num">
                  {p.largeur_mesuree_cm != null ? `${p.largeur_mesuree_cm}×${p.hauteur_mesuree_cm}` : "—"}
                </td>
                <td className="px-5 py-2.5 font-mono-num">{p.erreur_cm != null ? `${p.erreur_cm}cm` : "—"}</td>
                <td className="px-5 py-2.5">
                  <Badge variant={VARIANT_BY_VERDICT[p.verdict] ?? "neutral"}>{p.verdict}</Badge>
                </td>
              </tr>
            ))}
          </tbody>
        </table>
      </div>
    </Card>
  );
}
