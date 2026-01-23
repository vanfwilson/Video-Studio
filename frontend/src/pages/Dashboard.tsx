import React from "react";
import { Link } from "react-router-dom";
import { Play, AlertTriangle, ExternalLink, Trash2, RefreshCw } from "lucide-react";
import { listVideos, deleteVideo, prettyError } from "../api/videoApi";
import { Button, Card, Spinner, StatusPill, useToast } from "../components/ui";
import type { Video } from "../types";

export default function Dashboard() {
  const toast = useToast();
  const [loading, setLoading] = React.useState(true);
  const [videos, setVideos] = React.useState<Video[]>([]);
  const [error, setError] = React.useState<string | null>(null);

  const refresh = async () => {
    setError(null);
    setLoading(true);
    try {
      const data = await listVideos();
      setVideos(data.sort((a, b) => (b.id || 0) - (a.id || 0)));
    } catch (e) {
      setError(prettyError(e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    refresh();
  }, []);

  const handleDelete = async (video: Video) => {
    if (!confirm(`Delete "${video.title || video.original_filename}"?`)) return;
    try {
      await deleteVideo(video.id);
      toast.push({ type: "success", message: "Video deleted" });
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    }
  };

  const formatFileSize = (bytes?: number) => {
    if (!bytes) return "";
    const mb = bytes / 1024 / 1024;
    return mb > 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(1)} KB`;
  };

  const formatDate = (dateStr?: string) => {
    if (!dateStr) return "";
    return new Date(dateStr).toLocaleDateString("en-US", {
      month: "short",
      day: "numeric",
      hour: "2-digit",
      minute: "2-digit"
    });
  };

  return (
    <div className="space-y-6">
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div>
          <h1 className="text-2xl font-bold text-slate-900">Dashboard</h1>
          <p className="text-slate-600">
            Your videos, captions, metadata, and publish status
          </p>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={refresh} disabled={loading}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Link to="/upload">
            <Button>Upload Video</Button>
          </Link>
        </div>
      </div>

      {loading && <Spinner label="Loading videos..." />}

      {error && (
        <Card className="border-red-200 bg-red-50">
          <div className="text-red-800">{error}</div>
          <Button variant="secondary" onClick={refresh} className="mt-2">
            Try again
          </Button>
        </Card>
      )}

      {!loading && !error && videos.length === 0 && (
        <Card className="text-center py-12">
          <Play className="w-12 h-12 text-slate-400 mx-auto mb-4" />
          <h3 className="text-lg font-semibold text-slate-900 mb-2">No videos yet</h3>
          <p className="text-slate-600 mb-4">Upload your first video to get started</p>
          <Link to="/upload">
            <Button>Upload Video</Button>
          </Link>
        </Card>
      )}

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        {videos.map((video) => (
          <Card key={video.id} className="flex flex-col">
            {/* Video Preview */}
            <div className="relative aspect-video bg-slate-900 rounded-lg overflow-hidden mb-3">
              <video
                src={video.storage_path}
                className="w-full h-full object-contain"
                preload="metadata"
              />
              {video.youtube_url && (
                <a
                  href={video.youtube_url}
                  target="_blank"
                  rel="noopener noreferrer"
                  className="absolute top-2 right-2 bg-red-600 text-white px-2 py-1 rounded text-xs flex items-center gap-1"
                >
                  <ExternalLink className="w-3 h-3" />
                  YouTube
                </a>
              )}
            </div>

            {/* Video Info */}
            <div className="flex-1">
              <h3 className="font-semibold text-slate-900 truncate">
                {video.title || video.original_filename}
              </h3>
              <p className="text-xs text-slate-500 mt-1">
                {formatFileSize(video.file_size)} • {formatDate(video.created_at)}
              </p>

              <div className="flex flex-wrap gap-1 mt-2">
                <StatusPill status={video.status} />
                {video.confidentiality_status !== "pending" && (
                  <StatusPill status={video.confidentiality_status} />
                )}
              </div>

              {video.error_message && (
                <div className="mt-2 text-xs text-red-600 flex items-start gap-1">
                  <AlertTriangle className="w-3 h-3 mt-0.5 flex-shrink-0" />
                  {video.error_message}
                </div>
              )}
            </div>

            {/* Actions */}
            <div className="flex items-center justify-between mt-4 pt-3 border-t border-slate-100">
              <Link to={`/video/${video.id}`}>
                <Button variant="secondary" className="text-xs">
                  Edit & Publish
                </Button>
              </Link>
              <button
                onClick={() => handleDelete(video)}
                className="p-2 text-slate-400 hover:text-red-600 transition-colors"
                title="Delete video"
              >
                <Trash2 className="w-4 h-4" />
              </button>
            </div>
          </Card>
        ))}
      </div>
    </div>
  );
}
