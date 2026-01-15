import React from "react";
import { useParams, Link } from "react-router-dom";
import { getVideo, publishVideo } from "../api/videoApi";
import type { Video } from "../types";
import PublishPanel from "../components/PublishPanel";

export default function Publish() {
  const { id } = useParams();
  const videoId = id!;
  const [video, setVideo] = React.useState<Video | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    const v = await getVideo(videoId);
    setVideo(v);
  }, [videoId]);

  React.useEffect(() => {
    load().catch((e: any) => setError(e?.message || "Failed to load"));
  }, [load]);

  const onPublish = async () => {
    if (!video) return;
    setBusy(true);
    setError(null);
    try {
      const res = await publishVideo(videoId, {
        title: video.title || undefined,
        description: video.description || undefined,
        tags: video.tags || undefined,
        privacy_status: "private"
      });
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Publish failed");
    } finally {
      setBusy(false);
    }
  };

  if (!video) return <div className="text-slate-400">Loading…</div>;

  return (
    <div className="space-y-4">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-semibold">Publish</div>
          <div className="text-sm text-slate-400">{video.title || video.original_filename}</div>
        </div>
        <Link to={`/editor/${video.id}`} className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700">
          Back to Editor
        </Link>
      </div>

      {error ? <div className="text-red-300">{error}</div> : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
          <div className="text-sm font-medium">Preview</div>
          <video className="w-full rounded-lg border border-slate-800" controls src={video.storage_path} />
          <div className="text-xs text-slate-500">
            Confidentiality: <span className="text-slate-200">{video.confidentiality_status || "unknown"}</span>
          </div>
        </div>

        <PublishPanel youtubeUrl={video.youtube_url} onPublish={onPublish} loading={busy} />
      </div>
    </div>
  );
}
