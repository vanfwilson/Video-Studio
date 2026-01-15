import React from "react";
import { Link } from "react-router-dom";
import { listVideos } from "../api/videoApi";
import type { Video } from "../types";
import VideoCard from "../components/VideoCard";

export default function Dashboard() {
  const [videos, setVideos] = React.useState<Video[]>([]);
  const [loading, setLoading] = React.useState(true);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setLoading(true);
    setError(null);
    try {
      const data = await listVideos();
      setVideos(data);
    } catch (e: any) {
      setError(e?.message || "Failed to load videos");
    } finally {
      setLoading(false);
    }
  }, []);

  React.useEffect(() => {
    load();
  }, [load]);

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-semibold">Dashboard</div>
          <div className="text-sm text-slate-400">Your videos and publish status</div>
        </div>
        <Link to="/upload" className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500">
          Upload video
        </Link>
      </div>

      {loading ? <div className="text-slate-400">Loading…</div> : null}
      {error ? <div className="text-red-300">{error}</div> : null}

      <div className="grid grid-cols-1 gap-3">
        {videos.map((v) => (
          <VideoCard key={String(v.id)} v={v} />
        ))}
      </div>

      {!loading && videos.length === 0 ? (
        <div className="text-slate-500">No videos yet. Upload one to get started.</div>
      ) : null}
    </div>
  );
}
