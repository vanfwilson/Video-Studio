import React from "react";
import { useNavigate } from "react-router-dom";
import { uploadVideo, ingestFromUrl, prettyError } from "../api/videoApi";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Field, Input } from "../components/Field";
import { useToast } from "../components/Toasts";

export default function UploadPage() {
  const toast = useToast();
  const nav = useNavigate();
  const [busy, setBusy] = React.useState(false);
  const [file, setFile] = React.useState<File | null>(null);

  const [url, setUrl] = React.useState("");
  const [filename, setFilename] = React.useState("");

  const onUpload = async () => {
    if (!file) return;
    setBusy(true);
    try {
      const v = await uploadVideo(file);
      toast.push({ type: "success", message: "Upload complete. Continue to metadata." });
      nav(`/video/${v.id}/metadata`);
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  const onIngest = async () => {
    if (!url.trim()) return;
    setBusy(true);
    try {
      const v = await ingestFromUrl(url.trim(), filename.trim() || undefined);
      toast.push({ type: "success", message: "Ingest created. Continue to captions." });
      nav(`/video/${v.id}/captions`);
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  return (
    <div className="space-y-4">
      <div>
        <h1 className="text-xl font-semibold">Upload / Ingest</h1>
        <p className="text-sm text-slate-600">
          Upload a file directly, or ingest a public URL (cloud/file manager can generate one).
        </p>
      </div>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <div className="text-sm font-semibold">Direct upload</div>
          <input
            type="file"
            accept="video/*"
            onChange={(e) => setFile(e.target.files?.[0] || null)}
            className="block w-full text-sm"
          />
          {file && (
            <div className="text-xs text-slate-600">
              Selected: <span className="font-mono">{file.name}</span> ({Math.round(file.size / 1024 / 1024)} MB)
            </div>
          )}
          <Button onClick={onUpload} busy={busy} disabled={!file}>
            Upload
          </Button>
          <div className="text-xs text-slate-500">
            After upload you can request captions (n8n), generate metadata, then publish.
          </div>
        </Card>

        <Card className="space-y-3">
          <div className="text-sm font-semibold">Ingest existing video URL</div>
          <Field label="Public Video URL" hint="Used by n8n /transcribe">
            <Input value={url} onChange={(e) => setUrl(e.target.value)} placeholder="https://your-domain/uploads/video.mp4" />
          </Field>
          <Field label="Optional filename" hint="Helps label the video">
            <Input value={filename} onChange={(e) => setFilename(e.target.value)} placeholder="my-video.mp4" />
          </Field>
          <Button variant="secondary" onClick={onIngest} busy={busy} disabled={!url.trim()}>
            Create ingest
          </Button>
          <div className="text-xs text-slate-500">
            This matches your previous “sitting file in front of it” workflow.
          </div>
        </Card>
      </div>
    </div>
  );
}
