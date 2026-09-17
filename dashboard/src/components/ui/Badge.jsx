import React from "react";

const VARIANTS = {
  success: "bg-success-soft text-success border-success/20",
  warning: "bg-warning-soft text-warning border-warning/20",
  error: "bg-error-soft text-error border-error/20",
  neutral: "bg-sunken text-muted border-border",
};

export default function Badge({ variant = "neutral", children, dot = false }) {
  return (
    <span
      className={`inline-flex items-center gap-1.5 px-2.5 py-1 rounded-sm text-xs font-medium border ${VARIANTS[variant]}`}
    >
      {dot && (
        <span
          className="w-1.5 h-1.5 rounded-full"
          style={{ backgroundColor: "currentColor" }}
        />
      )}
      {children}
    </span>
  );
}
