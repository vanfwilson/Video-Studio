import React from "react";
import { Link } from "react-router-dom";
import { listVideos, prettyError } from "../api/videoApi";
import type { Video } from "../types";
import { Card } from "../components/Card";
import { Spinner } from "../components/Spinner";
import { StatusPill } from "../components/StatusPill";
import { Button } from "../components/Button";
import { useToast } from "../components/Toasts";

export default function Dashboard() {
  const toast = useToast();
  const [loading, setLoading] = React.useState(true);
  const [items, setItems] = React.useState<Video[]>([]);
  const [err, setErr] = React.useState<string | null>(null);

  const refresh = async () => {
    setErr(null);
    setLoading(true);
    try {
      const vids = await listVideos();
      setItems(vids.sort((a, b) => (b.id ?? 0) - (a.id ?? 0)));
    } catch (e) {
      setErr(prettyError(e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { refresh(); }, []);

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <h1 className="text-xl font-semibold">Dashboard</h1>
          <p className="text-sm text-slate-600">Your videos, captions, metadata, and publish status.</p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={refresh} disabled={loading}>Refresh</Button>
          <Link to="/upload">
            <Button>Upload / Ingest</Button>
          </Link>
        </div>
      </div>

      {loading && <Spinner label="Loading videos..." />}

      {err && (
        <Card className="border-rose-200 bg-rose-50">
          <div className="text-sm text-rose-800">Error: {err}</div>
          <div className="mt-2">
            <Button variant="secondary" onClick={refresh}>Try again</Button>
          </div>
        </Card>
      )}

      {!loading && !err && items.length === 0 && (
        <Card>
          <div className="text-sm text-slate-700">No videos yet. Upload one to start.</div>
        </Card>
      )}

      <div className="grid grid-cols-1 gap-3 lg:grid-cols-2">
        {items.map((v) => (
          <Card key={v.id} className="flex flex-col gap-3">
            <div className="flex items-start justify-between gap-3">
              <div className="min-w-0">
                <div className="truncate text-sm font-semibold">
                  {v.title?.trim() ? v.title : v.original_filename}
                </div>
                <div className="mt-1 flex flex-wrap items-center gap-2">
                  <StatusPill status={v.status || "unknown"} />
                  {v.youtube_url && (
                    <a className="text-xs text-sky-700 underline" href={v.youtube_url} target="_blank" rel="noreferrer">
                      YouTube link
                    </a>
                  )}
                </div>
                {v.error_message && <div className="mt-2 text-xs text-rose-700">{v.error_message}</div>}
              </div>
              {v.thumbnail_url ? (
                <img src={v.thumbnail_url} className="h-16 w-28 rounded-lg object-cover border border-slate-200" />
              ) : (
                <div className="h-16 w-28 rounded-lg border border-slate-200 bg-slate-50" />
              )}
            </div>

            <div className="flex flex-wrap gap-2">
              <Link to={`/video/${v.id}/metadata`}><Button variant="secondary">Metadata</Button></Link>
              <Link to={`/video/${v.id}/captions`}><Button variant="secondary">Captions</Button></Link>
              <Link to={`/video/${v.id}/publish`}><Button>Publish</Button></Link>
              <Button
                variant="ghost"
                onClick={() => toast.push({ type: "info", message: `Video ID: ${v.id} • Path: ${v.storage_path}` })}
              >
                Details
              </Button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
