import React from "react";
import type { Video } from "../types";
import { Link } from "react-router-dom";

export default function VideoCard({ v }: { v: Video }) {
  return (
    <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 hover:border-slate-700 transition">
      <div className="flex items-start justify-between gap-4">
        <div className="min-w-0">
          <div className="font-semibold truncate">{v.title || v.original_filename}</div>
          <div className="text-xs text-slate-400 mt-1">
            Status: <span className="text-slate-200">{v.status}</span>
            {v.confidentiality_status ? (
              <>
                {" · "}Conf: <span className="text-slate-200">{v.confidentiality_status}</span>
              </>
            ) : null}
          </div>
          {v.youtube_url ? (
            <a className="text-xs text-indigo-300 hover:underline mt-2 inline-block" href={v.youtube_url} target="_blank" rel="noreferrer">
              YouTube: {v.youtube_url}
            </a>
          ) : null}
        </div>
        <div className="flex gap-2">
          <Link to={`/editor/${v.id}`} className="px-3 py-2 text-sm rounded-lg bg-slate-800 hover:bg-slate-700">
            Open
          </Link>
          <Link to={`/publish/${v.id}`} className="px-3 py-2 text-sm rounded-lg bg-indigo-600 hover:bg-indigo-500">
            Publish
          </Link>
        </div>
      </div>

      {v.storage_path ? (
        <div className="text-xs text-slate-500 mt-3 truncate">
          {v.storage_path}
        </div>
      ) : null}
    </div>
  );
}
