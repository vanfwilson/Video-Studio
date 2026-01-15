import React from "react";

export default function CaptionEditor({
  value,
  onChange
}: {
  value: string;
  onChange: (v: string) => void;
}) {
  return (
    <div className="space-y-2">
      <div className="text-sm font-medium">Captions (editable)</div>
      <textarea
        className="w-full h-64 rounded-lg border border-slate-800 bg-slate-950 p-3 font-mono text-xs text-slate-100 focus:outline-none focus:ring-2 focus:ring-indigo-500/40"
        value={value}
        onChange={(e) => onChange(e.target.value)}
        placeholder="SRT or text captions..."
      />
      <div className="text-xs text-slate-500">
        Tip: keep SRT numbering/timestamps if you want to preserve format.
      </div>
    </div>
  );
}
