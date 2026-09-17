import React, { useState } from "react";
import Header from "../components/layout/Header";
import Card from "../components/ui/Card";

function ToggleRow({ label, description, defaultChecked = false }) {
  const [checked, setChecked] = useState(defaultChecked);
  return (
    <div className="flex items-center justify-between py-3">
      <div>
        <div className="text-sm font-medium">{label}</div>
        {description && <div className="text-xs text-muted mt-0.5">{description}</div>}
      </div>
      <button
        onClick={() => setChecked((c) => !c)}
        className={`w-10 h-6 rounded-full relative transition-colors ${
          checked ? "bg-accent" : "bg-sunken"
        }`}
        aria-pressed={checked}
      >
        <span
          className={`absolute top-0.5 w-5 h-5 rounded-full bg-white shadow transition-transform ${
            checked ? "translate-x-4" : "translate-x-0.5"
          }`}
        />
      </button>
    </div>
  );
}

export default function Settings() {
  return (
    <>
      <Header title="Settings" subtitle="Station and inspection preferences" />
      <div className="p-8 max-w-2xl flex flex-col gap-6">
        <Card>
          <div className="text-xs text-muted mb-1">Detection</div>
          <div className="divide-y divide-border">
            <ToggleRow
              label="Auto-retry on low confidence"
              description="Re-run detection once if confidence falls below threshold"
              defaultChecked
            />
            <ToggleRow
              label="Strict position tolerance"
              description="Tighten the acceptable position margin"
            />
          </div>
        </Card>
        <Card>
          <div className="text-xs text-muted mb-1">Notifications</div>
          <div className="divide-y divide-border">
            <ToggleRow label="Alert on failed inspection" defaultChecked />
            <ToggleRow label="Daily summary email" />
          </div>
        </Card>
      </div>
    </>
  );
}
