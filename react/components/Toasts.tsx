import React from "react";
import { cn } from "../lib/utils";

type Toast = { id: string; type: "success" | "error" | "info"; message: string };

const ToastContext = React.createContext<{
  push: (t: Omit<Toast, "id">) => void;
} | null>(null);

export function ToastProvider({ children }: { children: React.ReactNode }) {
  const [items, setItems] = React.useState<Toast[]>([]);

  const push = (t: Omit<Toast, "id">) => {
    const id = crypto.randomUUID();
    setItems((prev) => [...prev, { ...t, id }]);
    setTimeout(() => setItems((prev) => prev.filter((x) => x.id !== id)), 3500);
  };

  return (
    <ToastContext.Provider value={{ push }}>
      {children}
      <div className="fixed bottom-4 right-4 z-50 flex w-[340px] flex-col gap-2">
        {items.map((t) => (
          <div
            key={t.id}
            className={cn(
              "rounded-xl border px-3 py-2 shadow-md",
              t.type === "success" && "border-emerald-200 bg-emerald-50 text-emerald-900",
              t.type === "error" && "border-rose-200 bg-rose-50 text-rose-900",
              t.type === "info" && "border-sky-200 bg-sky-50 text-sky-900"
            )}
          >
            {t.message}
          </div>
        ))}
      </div>
    </ToastContext.Provider>
  );
}

export function useToast() {
  const ctx = React.useContext(ToastContext);
  if (!ctx) throw new Error("useToast must be used within ToastProvider");
  return ctx;
}
