import React from "react";
import type { ConfidentialityResult } from "../types";

export default function ConfidentialityPanel({
  status,
  result,
  onRun,
  loading
}: {
  status?: string | null;
  result?: ConfidentialityResult | null;
  onRun: () => void;
  loading: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
      <div className="flex items-center justify-between gap-3">
        <div>
          <div className="font-medium">Confidentiality check</div>
          <div className="text-xs text-slate-400">Status: {status || "unknown"}</div>
        </div>
        <button
          className="px-3 py-2 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50"
          onClick={onRun}
          disabled={loading}
        >
          {loading ? "Running..." : "Run check"}
        </button>
      </div>

      {result ? (
        <div className="text-sm space-y-2">
          <div className="text-slate-200">
            Overall: <span className="font-semibold">{result.overall_status}</span>
          </div>
          {result.summary ? <div className="text-slate-300">{result.summary}</div> : null}
          {result.counts ? (
            <div className="text-xs text-slate-400">
              High: {result.counts.high} · Medium: {result.counts.medium} · Low: {result.counts.low}
            </div>
          ) : null}
          {result.segments?.length ? (
            <div className="mt-2 space-y-2">
              <div className="text-xs text-slate-400">Findings</div>
              {result.segments.slice(0, 6).map((s, idx) => (
                <div key={idx} className="rounded-lg border border-slate-800 p-2 text-xs">
                  <div className="text-slate-200 font-medium">{s.risk}</div>
                  <div className="text-slate-300">{s.reason}</div>
                  <div className="text-slate-500 mt-1 italic">{s.snippet}</div>
                </div>
              ))}
            </div>
          ) : null}
        </div>
      ) : (
        <div className="text-xs text-slate-500">No results yet.</div>
      )}
    </div>
  );
}
