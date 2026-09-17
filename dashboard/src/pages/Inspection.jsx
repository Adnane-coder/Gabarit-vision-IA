import React from "react";
import Header from "../components/layout/Header";
import TraceeSelector from "../components/inspection/TraceeSelector";
import ConformitySummary from "../components/inspection/ConformitySummary";
import PieceVerdictTable from "../components/inspection/PieceVerdictTable";

export default function Inspection() {
  return (
    <>
      <Header title="Inspection" subtitle="Choisir un tracé et lancer le contrôle de conformité" />
      <div className="p-8 flex flex-col gap-6 max-w-5xl">
        <div className="grid grid-cols-1 md:grid-cols-[320px_1fr] gap-6">
          <TraceeSelector />
          <ConformitySummary />
        </div>
        <PieceVerdictTable />
      </div>
    </>
  );
}
