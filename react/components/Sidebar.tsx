// src/components/Sidebar.tsx
import { NavLink } from "react-router-dom";
import { cn } from "../lib/utils";

const nav = [
  { to: "/", label: "Dashboard" },
  { to: "/upload", label: "Upload / Ingest" }
];

export function Sidebar() {
  return (
    <aside className="hidden w-64 flex-shrink-0 border-r border-slate-200 bg-white p-4 md:block">
      <div className="mb-6">
        <div className="text-lg font-semibold">Video Studio</div>
        <div className="text-xs text-slate-500">Captions • Clips • Publish</div>
      </div>

      <nav className="flex flex-col gap-1">
        {nav.map((n) => (
          <NavLink
            key={n.to}
            to={n.to}
            className={({ isActive }) =>
              cn(
                "rounded-xl px-3 py-2 text-sm transition",
                isActive ? "bg-slate-900 text-white" : "text-slate-700 hover:bg-slate-50"
              )
            }
          >
            {n.label}
          </NavLink>
        ))}
      </nav>

      <div className="mt-6 rounded-2xl border border-slate-200 bg-slate-50 p-3 text-xs text-slate-600">
        Tip: Set <span className="font-mono">VITE_API_BASE_URL</span> to your FastAPI URL.
      </div>
    </aside>
  );
}
