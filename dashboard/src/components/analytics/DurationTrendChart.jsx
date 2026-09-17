import React from "react";
import { BarChart, Bar, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import Card from "../ui/Card";

export default function DurationTrendChart({ history }) {
  const data = [...history].reverse().map((h, i) => ({
    n: i + 1,
    seconds: Math.round(h.processing_time_ms / 100) / 10,
  }));

  return (
    <Card>
      <div className="text-xs text-muted mb-4">Temps de traitement (s) — dernières inspections</div>
      {data.length === 0 ? (
        <p className="text-sm text-muted py-16 text-center">Aucune inspection pour l'instant.</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <BarChart data={data} margin={{ left: -20, right: 10 }}>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="n" tick={{ fontSize: 12, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
            <YAxis tick={{ fontSize: 12, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} width={30} />
            <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
            <Bar dataKey="seconds" fill="var(--accent)" radius={[4, 4, 0, 0]} maxBarSize={28} />
          </BarChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
