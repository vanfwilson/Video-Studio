import { cn } from "../lib/utils";

export function StatusPill({ status }: { status: string }) {
  const s = (status || "").toLowerCase();
  const cls =
    s.includes("error") ? "bg-rose-50 text-rose-700 border-rose-200" :
    s.includes("publish") ? "bg-emerald-50 text-emerald-700 border-emerald-200" :
    s.includes("caption") || s.includes("process") ? "bg-amber-50 text-amber-700 border-amber-200" :
    "bg-slate-50 text-slate-700 border-slate-200";
  return <span className={cn("inline-flex items-center rounded-full border px-2.5 py-1 text-xs font-medium", cls)}>{status}</span>;
}
