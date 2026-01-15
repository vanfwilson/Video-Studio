import React from "react";

export default function PublishPanel({
  youtubeUrl,
  onPublish,
  loading
}: {
  youtubeUrl?: string | null;
  onPublish: () => void;
  loading: boolean;
}) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
      <div className="flex items-center justify-between">
        <div>
          <div className="font-medium">Publish</div>
          <div className="text-xs text-slate-400">Uses n8n workflow to publish to YouTube</div>
        </div>
        <button
          className="px-3 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
          onClick={onPublish}
          disabled={loading}
        >
          {loading ? "Publishing..." : "Publish"}
        </button>
      </div>

      {youtubeUrl ? (
        <a className="text-sm text-indigo-300 hover:underline" href={youtubeUrl} target="_blank" rel="noreferrer">
          Published: {youtubeUrl}
        </a>
      ) : (
        <div className="text-xs text-slate-500">Not published yet.</div>
      )}
    </div>
  );
}
