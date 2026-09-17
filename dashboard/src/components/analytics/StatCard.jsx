import React from "react";
import Card from "../ui/Card";

export default function StatCard({ value, label, tone = "ink" }) {
  const toneClass = {
    ink: "text-ink",
    success: "text-success",
    error: "text-error",
  }[tone];

  return (
    <Card className="flex flex-col gap-1">
      <div className={`font-mono-num text-3xl font-semibold ${toneClass}`}>{value}</div>
      <div className="text-xs text-muted">{label}</div>
    </Card>
  );
}
