import React from "react";
import { cn } from "../lib/utils";

type Props = React.ButtonHTMLAttributes<HTMLButtonElement> & {
  variant?: "primary" | "secondary" | "ghost" | "danger";
  busy?: boolean;
};

export function Button({ className, variant = "primary", busy, disabled, ...rest }: Props) {
  return (
    <button
      className={cn(
        "inline-flex items-center justify-center gap-2 rounded-xl px-4 py-2 text-sm font-medium transition",
        "focus:outline-none focus:ring-2 focus:ring-slate-300",
        variant === "primary" && "bg-slate-900 text-white hover:bg-slate-800",
        variant === "secondary" && "bg-white text-slate-900 border border-slate-200 hover:bg-slate-50",
        variant === "ghost" && "bg-transparent text-slate-900 hover:bg-slate-100",
        variant === "danger" && "bg-rose-600 text-white hover:bg-rose-700",
        (disabled || busy) && "opacity-60 cursor-not-allowed",
        className
      )}
      disabled={disabled || busy}
      {...rest}
    >
      {busy && (
        <span className="inline-block h-4 w-4 animate-spin rounded-full border-2 border-white/40 border-t-white" />
      )}
      {rest.children}
    </button>
  );
}
