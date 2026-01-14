import React from "react";
import { Link, useNavigate, useParams } from "react-router-dom";
import {
  getVideo,
  getYouTubeStatus,
  prettyError,
  publishToYouTube,
  startYouTubeOAuth
} from "../api/videoApi";
import { Card } from "../components/Card";
import { Button } from "../components/Button";
import { Spinner } from "../components/Spinner";
import { Field, Input, Select, Textarea } from "../components/Field";
import { useToast } from "../components/Toasts";
import type { PrivacyStatus, Video } from "../types";

export default function PublishPage() {
  const toast = useToast();
  const nav = useNavigate();
  const { id } = useParams();
  const videoId = Number(id);

  const [loading, setLoading] = React.useState(true);
  const [busy, setBusy] = React.useState(false);
  const [video, setVideo] = React.useState<Video | null>(null);
  const [connected, setConnected] = React.useState(false);
  const [ytName, setYtName] = React.useState<string | undefined>();
  const [ytChannel, setYtChannel] = React.useState<string | undefined>();

  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [tags, setTags] = React.useState("");
  const [privacy, setPrivacy] = React.useState<PrivacyStatus>("private");

  const refresh = async () => {
    setLoading(true);
    try {
      const [v, s] = await Promise.all([getVideo(videoId), getYouTubeStatus()]);
      setVideo(v);
      setTitle(v.title || v.original_filename);
      setDescription(v.description || "");
      setTags(v.tags || "");
      setPrivacy((v.privacy_status as PrivacyStatus) || "private");

      setConnected(Boolean(s.connected));
      setYtName(s.account?.account_name);
      setYtChannel(s.account?.channel_id);
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => { refresh(); }, [videoId]);

  const onConnect = async () => {
    setBusy(true);
    try {
      const { auth_url } = await startYouTubeOAuth();
      // send user to Google consent; Google redirects to /oauth/youtube/callback
      window.location.href = auth_url;
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
      setBusy(false);
    }
  };

  const onPublish = async () => {
    setBusy(true);
    try {
      const res = await publishToYouTube({
        video_id: videoId,
        title,
        description,
        tags,
        privacy_status: privacy
      });

      toast.push({ type: "success", message: res.youtube_url ? `Published: ${res.youtube_url}` : "Publish requested." });
      await refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  if (loading) return <Spinner label="Loading publish page..." />;
  if (!video) return <Card>Video not found.</Card>;

  return (
    <div className="space-y-4">
      <div className="flex flex-wrap items-start justify-between gap-3">
        <div>
          <h1 className="text-xl font-semibold">Publish</h1>
          <p className="text-sm text-slate-600">
            Connect your YouTube account, then publish to your channel.
          </p>
        </div>
        <div className="flex gap-2">
          <Link to={`/video/${videoId}/metadata`}><Button variant="secondary">Metadata</Button></Link>
          <Link to={`/video/${videoId}/captions`}><Button variant="secondary">Captions</Button></Link>
          <Link to="/"><Button variant="ghost">Dashboard</Button></Link>
        </div>
      </div>

      <Card className="flex flex-wrap items-center justify-between gap-3">
        <div>
          <div className="text-sm font-semibold">YouTube connection</div>
          <div className="text-xs text-slate-600">
            Status:{" "}
            {connected ? (
              <span className="text-emerald-700">Connected {ytName ? `as ${ytName}` : ""}{ytChannel ? ` • ${ytChannel}` : ""}</span>
            ) : (
              <span className="text-rose-700">Not connected</span>
            )}
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant={connected ? "secondary" : "primary"} onClick={onConnect} busy={busy}>
            {connected ? "Reconnect" : "Connect YouTube"}
          </Button>
          <Button variant="secondary" onClick={refresh} disabled={busy}>Refresh</Button>
        </div>
      </Card>

      <div className="grid grid-cols-1 gap-4 lg:grid-cols-2">
        <Card className="space-y-3">
          <div className="text-sm font-semibold">Publish settings</div>

          <Field label="Title">
            <Input value={title} onChange={(e) => setTitle(e.target.value)} />
          </Field>

          <Field label="Tags" hint="Comma-separated">
            <Input value={tags} onChange={(e) => setTags(e.target.value)} />
          </Field>

          <Field label="Privacy">
            <Select value={privacy} onChange={(e) => setPrivacy(e.target.value as PrivacyStatus)}>
              <option value="private">Private</option>
              <option value="unlisted">Unlisted</option>
              <option value="public">Public</option>
            </Select>
          </Field>

          <Button onClick={onPublish} busy={busy} disabled={!connected}>
            Publish to YouTube
          </Button>

          {!connected && (
            <div className="text-xs text-rose-700">
              Connect YouTube to publish (per-user channel).
            </div>
          )}

          {video.youtube_url && (
            <div className="text-xs">
              Published:{" "}
              <a className="text-sky-700 underline" href={video.youtube_url} target="_blank" rel="noreferrer">
                {video.youtube_url}
              </a>
            </div>
          )}
        </Card>

        <Card className="space-y-2">
          <div className="text-sm font-semibold">Description</div>
          <Textarea rows={16} value={description} onChange={(e) => setDescription(e.target.value)} />
          <div className="text-xs text-slate-500">
            Tip: include links, CTA, and a hashtag line at the end.
          </div>
        </Card>
      </div>

      <Card className="flex items-center justify-between">
        <div className="text-xs text-slate-600">
          If publish fails, check backend logs + stored refresh token. You can reconnect.
        </div>
        <Button variant="ghost" onClick={() => nav(0)}>Reload page</Button>
      </Card>
    </div>
  );
}
