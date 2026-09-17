import React from "react";
import { AreaChart, Area, XAxis, YAxis, Tooltip, ResponsiveContainer, CartesianGrid } from "recharts";
import Card from "../ui/Card";

export default function ConfidenceTrendChart({ history }) {
  const data = [...history].reverse().map((h, i) => ({
    n: i + 1,
    confidence: Math.round(h.confidence * 1000) / 10,
  }));

  return (
    <Card>
      <div className="text-xs text-muted mb-4">Taux de conformité — dernières inspections</div>
      {data.length === 0 ? (
        <p className="text-sm text-muted py-16 text-center">Aucune inspection pour l'instant.</p>
      ) : (
        <ResponsiveContainer width="100%" height={220}>
          <AreaChart data={data} margin={{ left: -20, right: 10 }}>
            <defs>
              <linearGradient id="confFill" x1="0" y1="0" x2="0" y2="1">
                <stop offset="0%" stopColor="var(--success)" stopOpacity={0.25} />
                <stop offset="100%" stopColor="var(--success)" stopOpacity={0} />
              </linearGradient>
            </defs>
            <CartesianGrid stroke="var(--border)" vertical={false} />
            <XAxis dataKey="n" tick={{ fontSize: 12, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} />
            <YAxis domain={[0, 100]} tick={{ fontSize: 12, fill: "var(--text-muted)" }} axisLine={false} tickLine={false} width={36} />
            <Tooltip contentStyle={{ background: "var(--surface)", border: "1px solid var(--border)", borderRadius: 8, fontSize: 12 }} />
            <Area type="monotone" dataKey="confidence" stroke="var(--success)" strokeWidth={2} fill="url(#confFill)" />
          </AreaChart>
        </ResponsiveContainer>
      )}
    </Card>
  );
}
