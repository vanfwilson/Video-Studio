import React from "react";
import { Link, useParams } from "react-router-dom";
import { getVideo, prettyError, requestCaptions, saveCaptions } from "../api/videoApi";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";
import { Textarea } from "../components/Field";
import { useToast } from "../components/Toasts";
import type { Video } from "../types";

function guessTranscriptFromSrt(srt: string): string {
  // very lightweight: remove indices + timestamps
  return srt
    .split("\n")
    .filter((line) => !/^\d+$/.test(line.trim()))
    .filter((line) => !/-->\s/.test(line))
    .join(" ")
    .replace(/\s+/g, " ")
    .trim();
}

export default function CaptionsPage() {
  const toast = useToast();
  const { id } = useParams();
  const videoId = Number(id);

  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [video, setVideo] = React.useState<Video | null>(null);
  const [err, setErr] = React.useState<string | null>(null);

  const [captionsText, setCaptionsText] = React.useState("");
  const [transcript, setTranscript] = React.useState("");

  const refresh = async () => {
    setErr(null);
    setLoading(true);
    try {
      const v = await getVideo(videoId);
      setVideo(v);
      setCaptionsText(v.captions || "");
      setTranscript(v.transcript || "");
    } catch (e) {
      setErr(prettyError(e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { refresh(); }, [videoId]);

  const onRequest = async () => {
    setBusy(true);
    try {
      const res = await requestCaptions(videoId);
      const text = res.captions || "";
      setCaptionsText(text);
      if (!transcript && res.captions_format === "srt") {
        setTranscript(guessTranscriptFromSrt(text));
      }
      toast.push({ type: "success", message: `Captions received (${res.captions_format}).` });
      await refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  const onSave = async () => {
    setBusy(true);
    try {
      await saveCaptions(videoId, captionsText, transcript);
      toast.push({ type: "success", message: "Captions saved." });
      await refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <Spinner label="Loading video..." />;

  if (err || !video) {
    return (
      <Card className="border-rose-200 bg-rose-50">
        <div className="text-sm text-rose-800">{err || "Video not found"}</div>
        <div className="mt-2"><Link to="/"><Button variant="secondary">Back</Button></Link></div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Captions</h1>
          <p className="text-sm text-slate-600">
            n8n transcription expects a <span className="font-medium">public video_url</span>.
          </p>
          <p className="text-xs text-slate-500">
            storage_path: <span className="font-mono">{video.storage_path}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/video/${videoId}/metadata`}><Button variant="secondary">Metadata</Button></Link>
          <Link to={`/video/${videoId}/publish`}><Button>Publish</Button></Link>
        </div>
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-2">
        <div className="text-sm text-slate-700">
          Current status: <span className="font-mono">{video.status}</span>
        </div>
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={onRequest} busy={busy}>Request captions</Button>
          <Button onClick={onSave} busy={busy} disabled={!captionsText.trim() && !transcript.trim()}>
            Save
          </Button>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-2">
          <div className="text-sm font-semibold">SRT (preferred) or plain text</div>
          <Textarea rows={18} value={captionsText} onChange={(e) => setCaptionsText(e.target.value)} placeholder="SRT will appear here..." />
          <div className="text-xs text-slate-500">
            If you paste/modify SRT, Save will store it to <span className="font-mono">videos.captions</span>.
          </div>
        </Card>

        <Card className="space-y-2">
          <div className="text-sm font-semibold">Transcript (optional / fallback)</div>
          <Textarea rows={18} value={transcript} onChange={(e) => setTranscript(e.target.value)} placeholder="Plain transcript..." />
          <div className="text-xs text-slate-500">
            Stored to <span className="font-mono">videos.transcript</span>. Useful for search/RAG and metadata generation.
          </div>
        </Card>
      </div>
    </div>
  );
}
