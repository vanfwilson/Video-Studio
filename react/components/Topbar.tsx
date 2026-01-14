// src/components/Topbar.tsx
import { UserSwitcher } from "./UserSwitcher";

export function Topbar() {
  return (
    <header className="flex items-center justify-between border-b border-slate-200 bg-white px-6 py-3">
      <div className="text-sm text-slate-600">
        Build: <span className="font-mono">{import.meta.env.MODE}</span>
      </div>
      <UserSwitcher />
    </header>
  );
}
