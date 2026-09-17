import React from "react";
import { motion } from "framer-motion";

export default function ProgressBar({ value = 0, tone = "accent" }) {
  const toneMap = {
    accent: "bg-accent",
    success: "bg-success",
    warning: "bg-warning",
    error: "bg-error",
  };

  return (
    <div className="w-full h-1.5 bg-sunken rounded-full overflow-hidden">
      <motion.div
        className={`h-full rounded-full ${toneMap[tone]}`}
        initial={{ width: 0 }}
        animate={{ width: `${value}%` }}
        transition={{ duration: 0.6, ease: "easeOut" }}
      />
    </div>
  );
}
