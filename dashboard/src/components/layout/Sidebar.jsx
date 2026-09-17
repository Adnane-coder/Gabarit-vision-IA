import React from "react";
import { NavLink } from "react-router-dom";
import { LayoutGrid, ScanEye, History, BarChart3, SlidersHorizontal, Aperture } from "lucide-react";

const NAV_ITEMS = [
  { to: "/", label: "Overview", icon: LayoutGrid, end: true },
  { to: "/inspection", label: "Inspection", icon: ScanEye },
  { to: "/history", label: "History", icon: History },
  { to: "/analytics", label: "Analytics", icon: BarChart3 },
  { to: "/settings", label: "Settings", icon: SlidersHorizontal },
];

export default function Sidebar() {
  return (
    <aside className="w-60 shrink-0 h-screen sticky top-0 flex flex-col border-r border-border bg-surface">
      <div className="flex items-center gap-2.5 px-5 h-16 border-b border-border">
        <div className="w-8 h-8 rounded-md bg-accent-soft flex items-center justify-center">
          <Aperture size={17} className="text-accent" strokeWidth={1.75} />
        </div>
        <div className="leading-tight">
          <div className="text-sm font-semibold">Control Center</div>
          <div className="text-[11px] text-muted">Quality Inspection</div>
        </div>
      </div>

      <nav className="flex-1 px-3 py-4 flex flex-col gap-1">
        {NAV_ITEMS.map(({ to, label, icon: Icon, end }) => (
          <NavLink
            key={to}
            to={to}
            end={end}
            className={({ isActive }) =>
              `group flex items-center gap-3 px-3 py-2.5 rounded-md text-sm transition-colors duration-150 ${
                isActive
                  ? "bg-accent-soft text-ink font-medium"
                  : "text-muted hover:bg-sunken hover:text-ink"
              }`
            }
          >
            {({ isActive }) => (
              <>
                <span
                  className={`w-1 h-4 rounded-full transition-colors ${
                    isActive ? "bg-accent" : "bg-transparent"
                  }`}
                />
                <Icon size={17} strokeWidth={1.75} />
                {label}
              </>
            )}
          </NavLink>
        ))}
      </nav>

      <div className="px-5 py-4 border-t border-border text-[11px] text-muted">
        Station 04 — Line B
      </div>
    </aside>
  );
}
