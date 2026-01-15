import React from "react";
import { useNavigate } from "react-router-dom";
import { uploadVideo, captionVideo } from "../api/videoApi";

export default function Upload() {
  const nav = useNavigate();
  const [file, setFile] = React.useState<File | null>(null);
  const [busy, setBusy] = React.useState(false);
  const [error, setError] = React.useState<string | null>(null);

  const onUpload = async () => {
    if (!file) return;
    setBusy(true);
    setError(null);
    try {
      const v = await uploadVideo(file);
      // Immediately start captions step (flow step 1 -> 2)
      await captionVideo(v.id, "en");
      nav(`/editor/${v.id}`);
    } catch (e: any) {
      setError(e?.response?.data?.detail || e?.message || "Upload failed");
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <div className="text-2xl font-semibold">Upload</div>
        <div className="text-sm text-slate-400">Upload a raw video, then captions are fetched via n8n</div>
      </div>

      <div className="rounded-xl border border-slate-800 bg-slate-950 p-4 space-y-3">
        <input
          type="file"
          accept="video/*"
          onChange={(e) => setFile(e.target.files?.[0] || null)}
          className="block w-full text-sm text-slate-300 file:mr-3 file:rounded-lg file:border-0 file:bg-slate-800 file:px-3 file:py-2 file:text-sm file:text-white hover:file:bg-slate-700"
        />

        <button
          onClick={onUpload}
          disabled={!file || busy}
          className="px-4 py-2 rounded-lg bg-indigo-600 hover:bg-indigo-500 disabled:opacity-50"
        >
          {busy ? "Uploading + Captioning..." : "Upload and fetch captions"}
        </button>

        {error ? <div className="text-red-300 text-sm">{error}</div> : null}
      </div>
    </div>
  );
}
