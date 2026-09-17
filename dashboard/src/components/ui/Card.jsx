import React from "react";

export default function Card({ children, className = "", padded = true }) {
  return (
    <div
      className={`bg-surface border border-border rounded-lg shadow-panel ${
        padded ? "p-5" : ""
      } ${className}`}
    >
      {children}
    </div>
  );
}
