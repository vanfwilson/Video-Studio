import React from "react";
import { Link, useParams } from "react-router-dom";
import { generateMetadata, getVideo, prettyError, updateVideoMetadata } from "../api/videoApi";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Field, Input, Textarea } from "../components/Field";
import { Spinner } from "../components/Spinner";
import { useToast } from "../components/Toasts";
import type { Video } from "../types";

export default function MetadataPage() {
  const toast = useToast();
  const { id } = useParams();
  const videoId = Number(id);

  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [video, setVideo] = React.useState<Video | null>(null);
  const [err, setErr] = React.useState<string | null>(null);

  // fields
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [tags, setTags] = React.useState("");
  const [hashtags, setHashtags] = React.useState("");
  const [prompt, setPrompt] = React.useState("Create a compelling YouTube title, description, tags, and hashtags.");

  const refresh = async () => {
    setErr(null);
    setLoading(true);
    try {
      const v = await getVideo(videoId);
      setVideo(v);
      setTitle(v.title || "");
      setDescription(v.description || "");
      setTags(v.tags || "");
      setHashtags((v.hashtags as any) || "");
    } catch (e) {
      setErr(prettyError(e));
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { refresh(); }, [videoId]);

  const onGenerate = async () => {
    setBusy(true);
    try {
      const res = await generateMetadata({
        video_id: videoId,
        prompt,
        model: "auto",
        tone: "punchy",
        hashtags: true
      });
      if (res.title) setTitle(res.title);
      if (res.description) setDescription(res.description);
      if (res.tags) setTags(res.tags);
      if (res.hashtags) setHashtags(res.hashtags);
      toast.push({ type: "success", message: "Generated metadata. Review and save." });
    } catch (e) {
      // If your backend doesn’t implement this yet, you still keep manual editing.
      toast.push({ type: "error", message: `Metadata generator unavailable: ${prettyError(e)}` });
    } finally {
      setBusy(false);
    }
  };

  const onSave = async () => {
    setBusy(true);
    try {
      await updateVideoMetadata(videoId, {
        title,
        description,
        tags,
        hashtags,
        status: "metadata_ready"
      });
      toast.push({ type: "success", message: "Saved metadata." });
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
        <div className="mt-2">
          <Link to="/"><Button variant="secondary">Back</Button></Link>
        </div>
      </Card>
    );
  }

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Metadata</h1>
          <p className="text-sm text-slate-600">
            Video: <span className="font-mono">{video.original_filename}</span>
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/video/${videoId}/captions`}><Button variant="secondary">Captions</Button></Link>
          <Link to={`/video/${videoId}/publish`}><Button>Publish</Button></Link>
        </div>
      </div>

      <Card className="space-y-3">
        <div className="text-sm font-semibold">AI prompt (optional)</div>
        <Textarea rows={3} value={prompt} onChange={(e) => setPrompt(e.target.value)} />
        <div className="flex flex-wrap gap-2">
          <Button variant="secondary" onClick={onGenerate} busy={busy}>Generate</Button>
          <Button onClick={onSave} busy={busy}>Save</Button>
        </div>
        <div className="text-xs text-slate-500">
          If AI generation is unavailable, edit manually and click Save.
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <Field label="Title" hint="Best under ~70 chars">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} placeholder="Your YouTube title..." />
          </Field>

          <Field label="Tags" hint="Comma-separated">
            <Input value={tags} onChange={(e) => setTags(e.target.value)} placeholder="tag1, tag2, tag3" />
          </Field>

          <Field label="Hashtags" hint="Space-separated or comma-separated">
            <Input value={hashtags} onChange={(e) => setHashtags(e.target.value)} placeholder="#shorts #marketing #ai" />
          </Field>
        </Card>

        <Card className="space-y-3">
          <Field label="Description" hint="Include CTA + links">
            <Textarea rows={12} value={description} onChange={(e) => setDescription(e.target.value)} />
          </Field>
        </Card>
      </div>
    </div>
  );
}
