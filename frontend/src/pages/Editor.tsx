import React from "react";
import { useParams, Link } from "react-router-dom";
import { getVideo, patchVideo, generateMetadata, runConfidentiality } from "../api/videoApi";
import type { Video, ConfidentialityResult } from "../types";
import CaptionEditor from "../components/CaptionEditor";
import MetadataForm from "../components/MetadataForm";
import ConfidentialityPanel from "../components/ConfidentialityPanel";

export default function Editor() {
  const { id } = useParams();
  const videoId = id!;
  const [video, setVideo] = React.useState<Video | null>(null);
  const [captions, setCaptions] = React.useState("");
  const [busySave, setBusySave] = React.useState(false);
  const [busyMeta, setBusyMeta] = React.useState(false);
  const [busyConf, setBusyConf] = React.useState(false);
  const [confRes, setConfRes] = React.useState<ConfidentialityResult | null>(null);
  const [error, setError] = React.useState<string | null>(null);

  const load = React.useCallback(async () => {
    setError(null);
    const v = await getVideo(videoId);
    setVideo(v);
    setCaptions(v.captions || "");
  }, [videoId]);

  React.useEffect(() => {
    load().catch((e: any) => setError(e?.message || "Failed to load"));
  }, [load]);

  const saveAll = async (patch: Partial<Video> & { captions?: string }) => {
    setBusySave(true);
    try {
      const updated = await patchVideo(videoId, patch);
      setVideo(updated);
      if (typeof patch.captions === "string") setCaptions(patch.captions);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Save failed");
    } finally {
      setBusySave(false);
    }
  };

  const onGenerate = async () => {
    setBusyMeta(true);
    setError(null);
    try {
      const res = await generateMetadata(videoId);
      // refresh video
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "AI metadata generation failed");
    } finally {
      setBusyMeta(false);
    }
  };

  const onConfidentiality = async () => {
    setBusyConf(true);
    setError(null);
    try {
      const res = await runConfidentiality(videoId);
      setConfRes(res);
      await load();
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Confidentiality check failed");
    } finally {
      setBusyConf(false);
    }
  };

  if (!video) {
    return <div className="text-slate-400">Loading editor…</div>;
  }

  return (
    <div className="space-y-5">
      <div className="flex items-center justify-between">
        <div>
          <div className="text-2xl font-semibold">Editor</div>
          <div className="text-sm text-slate-400">{video.original_filename}</div>
        </div>
        <div className="flex gap-2">
          <button
            className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50"
            disabled={busySave}
            onClick={() => saveAll({ captions })}
          >
            {busySave ? "Saving..." : "Save"}
          </button>
          <Link to={`/publish/${video.id}`} className="px-3 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500">
            Publish
          </Link>
        </div>
      </div>

      {error ? <div className="text-red-300">{error}</div> : null}

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-4">
        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
            <div className="text-sm font-medium">Preview</div>
            <video className="w-full rounded-lg border border-slate-800" controls src={video.storage_path} />
            {video.thumbnail_url ? (
              <img src={video.thumbnail_url} alt="thumbnail" className="w-full rounded-lg border border-slate-800" />
            ) : (
              <div className="text-xs text-slate-500">No thumbnail yet.</div>
            )}
          </div>

          <ConfidentialityPanel
            status={video.confidentiality_status}
            result={confRes}
            onRun={onConfidentiality}
            loading={busyConf}
          />
        </div>

        <div className="space-y-4">
          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-4">
            <div className="flex items-center justify-between">
              <div className="font-medium">AI content</div>
              <button
                className="px-3 py-2 text-sm rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50"
                disabled={busyMeta}
                onClick={onGenerate}
              >
                {busyMeta ? "Generating..." : "Generate metadata"}
              </button>
            </div>

            <div className="text-sm text-slate-300 whitespace-pre-wrap">
              {video.ai_summary || <span className="text-slate-500">No AI summary yet.</span>}
            </div>

            <MetadataForm
              title={video.title || ""}
              description={video.description || ""}
              tags={video.tags || ""}
              hashtags={video.hashtags || ""}
              thumbnailPrompt={video.thumbnail_prompt || ""}
              onChange={(p) => saveAll(p as any)}
            />
          </div>

          <div className="rounded-xl border border-slate-800 bg-slate-950 p-4">
            <CaptionEditor value={captions} onChange={setCaptions} />
            <div className="mt-3 flex gap-2">
              <button
                className="px-3 py-2 rounded-lg bg-slate-800 hover:bg-slate-700 disabled:opacity-50"
                disabled={busySave}
                onClick={() => saveAll({ captions })}
              >
                {busySave ? "Saving..." : "Save captions"}
              </button>
            </div>
          </div>
        </div>
      </div>
    </div>
  );
}
