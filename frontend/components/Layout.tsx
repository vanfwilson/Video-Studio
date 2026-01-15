import React from "react";
import { NavLink, Outlet } from "react-router-dom";

const navItem = (isActive: boolean) =>
  `px-3 py-2 rounded-lg text-sm ${isActive ? "bg-slate-800 text-white" : "text-slate-300 hover:bg-slate-900 hover:text-white"}`;

export default function Layout() {
  return (
    <div className="min-h-screen">
      <header className="border-b border-slate-800 bg-slate-950/70 backdrop-blur">
        <div className="mx-auto max-w-6xl px-4 py-4 flex items-center justify-between">
          <div className="flex items-center gap-3">
            <div className="h-9 w-9 rounded-xl bg-indigo-600/20 border border-indigo-500/30 grid place-items-center">
              <span className="font-bold text-indigo-200">VS</span>
            </div>
            <div>
              <div className="font-semibold leading-tight">Video Studio</div>
              <div className="text-xs text-slate-400">askstephen.ai</div>
            </div>
          </div>
          <nav className="flex items-center gap-2">
            <NavLink to="/" className={({ isActive }) => navItem(isActive)}>Dashboard</NavLink>
            <NavLink to="/upload" className={({ isActive }) => navItem(isActive)}>Upload</NavLink>
          </nav>
        </div>
      </header>

      <main className="mx-auto max-w-6xl px-4 py-6">
        <Outlet />
      </main>
    </div>
  );
}
