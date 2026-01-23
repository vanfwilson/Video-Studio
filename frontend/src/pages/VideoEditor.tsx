import React from "react";
import { useParams, useNavigate, Link } from "react-router-dom";
import {
  ArrowLeft,
  RefreshCw,
  Save,
  Youtube,
  Wand2,
  AlertTriangle,
  CheckCircle,
  Shield,
  FileText,
  ExternalLink
} from "lucide-react";
import {
  getVideo,
  updateVideo,
  requestCaptions,
  generateMetadata,
  checkConfidentiality,
  getYouTubeStatus,
  startYouTubeOAuth,
  publishToYouTube,
  prettyError,
  translateCaptions
} from "../api/videoApi";
import LanguageSelector from "../components/LanguageSelector";
import {
  Button,
  Card,
  Spinner,
  StatusPill,
  Field,
  Input,
  Textarea,
  Select,
  useToast
} from "../components/ui";
import type { Video, YouTubeAccount, PrivacyStatus } from "../types";

// Helper to extract existing caption languages from video
function getExistingCaptionLanguages(video: Video): string[] {
  if (!video.captions) return [];

  // If captions is a string, assume it's the source language
  if (typeof video.captions === "string") {
    return [video.language || "en"];
  }

  // If captions is an object, check if it's multi-language or legacy format
  if (typeof video.captions === "object") {
    const caps = video.captions as Record<string, any>;
    // Check for legacy format (has srt/text/content at top level)
    if ("srt" in caps || "text" in caps || "content" in caps || "format" in caps) {
      return [video.language || "en"];
    }
    // Multi-language format - keys are language codes
    return Object.keys(caps).filter(key =>
      typeof caps[key] === "object" || typeof caps[key] === "string"
    );
  }

  return [];
}

export default function VideoEditor() {
  const { id } = useParams();
  const navigate = useNavigate();
  const toast = useToast();
  const videoId = Number(id);

  // State
  const [loading, setLoading] = React.useState(true);
  const [video, setVideo] = React.useState<Video | null>(null);
  const [busy, setBusy] = React.useState<string | null>(null);

  // YouTube connection
  const [ytConnected, setYtConnected] = React.useState(false);
  const [ytAccount, setYtAccount] = React.useState<YouTubeAccount | null>(null);

  // Form state
  const [title, setTitle] = React.useState("");
  const [description, setDescription] = React.useState("");
  const [tags, setTags] = React.useState("");
  const [hashtags, setHashtags] = React.useState("");
  const [privacy, setPrivacy] = React.useState<PrivacyStatus>("private");
  const [captions, setCaptions] = React.useState("");
  const [transcript, setTranscript] = React.useState("");

  // Load video data
  const refresh = async () => {
    setLoading(true);
    try {
      const [v, yt] = await Promise.all([getVideo(videoId), getYouTubeStatus()]);
      setVideo(v);
      setTitle(v.title || v.original_filename);
      setDescription(v.description || "");
      setTags(v.tags || "");
      setHashtags(v.hashtags || "");
      setPrivacy(v.privacy_status || "private");
      setCaptions(v.captions || "");
      setTranscript(v.transcript || "");

      setYtConnected(yt.connected);
      setYtAccount(yt.account || null);
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setLoading(false);
    }
  };

  React.useEffect(() => {
    refresh();
  }, [videoId]);

  // Polling for processing states
  React.useEffect(() => {
    if (!video) return;
    if (video.status === "captioning" || video.status === "publishing") {
      const timer = setInterval(refresh, 3000);
      return () => clearInterval(timer);
    }
  }, [video?.status]);

  // Actions
  const handleSave = async () => {
    setBusy("save");
    try {
      await updateVideo(videoId, {
        title,
        description,
        tags,
        hashtags,
        privacy_status: privacy,
        captions,
        transcript
      });
      toast.push({ type: "success", message: "Saved!" });
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  const handleRequestCaptions = async () => {
    setBusy("captions");
    try {
      const result = await requestCaptions(videoId);
      setCaptions(result.captions);
      toast.push({ type: "success", message: `Captions received (${result.captions_format})` });
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  const handleGenerateMetadata = async () => {
    setBusy("metadata");
    try {
      const result = await generateMetadata(videoId);
      if (result.title) setTitle(result.title);
      if (result.description) setDescription(result.description);
      if (result.tags) setTags(result.tags);
      if (result.hashtags) setHashtags(result.hashtags);
      toast.push({ type: "success", message: "Metadata generated!" });
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  const handleConfidentialityCheck = async () => {
    setBusy("confidentiality");
    try {
      const result = await checkConfidentiality(videoId);
      toast.push({
        type: result.overall_status === "pass" ? "success" : "info",
        message: result.summary
      });
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  const handleConnectYouTube = async () => {
    setBusy("youtube");
    try {
      const { auth_url } = await startYouTubeOAuth();
      window.location.href = auth_url;
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
      setBusy(null);
    }
  };

  const handlePublish = async () => {
    if (!confirm("Publish this video to YouTube?")) return;
    setBusy("publish");
    try {
      const result = await publishToYouTube({
        video_id: videoId,
        title,
        description,
        tags,
        privacy_status: privacy
      });
      if (result.youtube_url) {
        toast.push({ type: "success", message: `Published! ${result.youtube_url}` });
      } else {
        toast.push({ type: "success", message: "Publishing..." });
      }
      refresh();
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  if (loading) return <Spinner label="Loading video..." />;
  if (!video) {
    return (
      <Card>
        <p className="text-red-600">Video not found</p>
        <Link to="/">
          <Button variant="secondary" className="mt-2">Back to Dashboard</Button>
        </Link>
      </Card>
    );
  }

  const isProcessing = video.status === "captioning" || video.status === "publishing";
  const isPublished = video.status === "published";
  const hasConfidentialityIssues = video.confidentiality_status === "warn" || video.confidentiality_status === "fail";

  return (
    <div className="space-y-6">
      {/* Header */}
      <div className="flex flex-wrap items-center justify-between gap-4">
        <div className="flex items-center gap-3">
          <button onClick={() => navigate("/")} className="text-slate-500 hover:text-slate-700">
            <ArrowLeft className="w-5 h-5" />
          </button>
          <div>
            <h1 className="text-2xl font-bold text-slate-900">Edit Video</h1>
            <p className="text-slate-600">{video.original_filename}</p>
          </div>
        </div>
        <div className="flex gap-2">
          <Button variant="secondary" onClick={refresh} disabled={!!busy}>
            <RefreshCw className="w-4 h-4" />
            Refresh
          </Button>
          <Button onClick={handleSave} busy={busy === "save"}>
            <Save className="w-4 h-4" />
            Save
          </Button>
        </div>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-3 gap-6">
        {/* Left Column - Video & Actions */}
        <div className="lg:col-span-1 space-y-4">
          {/* Video Preview */}
          <Card>
            <div className="aspect-video bg-slate-900 rounded-lg overflow-hidden mb-3">
              <video src={video.storage_path} controls className="w-full h-full" />
            </div>
            <div className="flex flex-wrap gap-2">
              <StatusPill status={video.status} />
              {video.confidentiality_status !== "pending" && (
                <StatusPill status={video.confidentiality_status} />
              )}
            </div>
          </Card>

          {/* Actions */}
          <Card className="space-y-3">
            <h3 className="font-semibold">AI Processing</h3>
            
            <Button
              variant="secondary"
              onClick={handleRequestCaptions}
              busy={busy === "captions"}
              disabled={isProcessing}
              className="w-full"
            >
              <FileText className="w-4 h-4" />
              Request Captions
            </Button>
            
            <Button
              variant="secondary"
              onClick={handleGenerateMetadata}
              busy={busy === "metadata"}
              disabled={isProcessing || !captions}
              className="w-full"
            >
              <Wand2 className="w-4 h-4" />
              Generate Metadata
            </Button>
            
            <Button
              variant="secondary"
              onClick={handleConfidentialityCheck}
              busy={busy === "confidentiality"}
              disabled={isProcessing || !transcript && !captions}
              className="w-full"
            >
              <Shield className="w-4 h-4" />
              Check Confidentiality
            </Button>
          </Card>

          {/* Confidentiality Warning */}
          {hasConfidentialityIssues && (
            <Card className="border-red-200 bg-red-50">
              <div className="flex items-start gap-3">
                <AlertTriangle className="w-5 h-5 text-red-600 flex-shrink-0" />
                <div>
                  <h4 className="font-semibold text-red-800">Confidentiality Issues</h4>
                  <ul className="mt-2 space-y-1 text-sm text-red-700">
                    {video.confidentiality_issues?.map((issue, i) => (
                      <li key={i} className="flex items-start gap-2">
                        <span className={`px-1.5 py-0.5 rounded text-xs ${
                          issue.risk === "high" ? "bg-red-200" : 
                          issue.risk === "medium" ? "bg-yellow-200" : "bg-blue-200"
                        }`}>
                          {issue.risk}
                        </span>
                        <span>{issue.reason}: "{issue.snippet}"</span>
                      </li>
                    ))}
                  </ul>
                </div>
              </div>
            </Card>
          )}

          {/* YouTube Connection */}
          <Card className="space-y-3">
            <h3 className="font-semibold">YouTube</h3>
            
            {ytConnected ? (
              <div className="flex items-center gap-2 text-sm text-green-700">
                <CheckCircle className="w-4 h-4" />
                Connected as {ytAccount?.account_name || "Unknown"}
              </div>
            ) : (
              <div className="text-sm text-slate-600">Not connected</div>
            )}
            
            <Button
              variant={ytConnected ? "secondary" : "primary"}
              onClick={handleConnectYouTube}
              busy={busy === "youtube"}
              className="w-full"
            >
              {ytConnected ? "Reconnect" : "Connect YouTube"}
            </Button>
            
            {isPublished && video.youtube_url && (
              <a
                href={video.youtube_url}
                target="_blank"
                rel="noopener noreferrer"
                className="flex items-center gap-2 text-sm text-primary-600 hover:underline"
              >
                <ExternalLink className="w-4 h-4" />
                View on YouTube
              </a>
            )}
          </Card>
        </div>

        {/* Right Column - Form */}
        <div className="lg:col-span-2 space-y-4">
          {/* Metadata */}
          <Card className="space-y-4">
            <h3 className="font-semibold">Metadata</h3>
            
            <Field label="Title" hint="Under 100 characters works best">
              <Input
                value={title}
                onChange={(e) => setTitle(e.target.value)}
                maxLength={100}
              />
              <p className="text-xs text-slate-400 mt-1">{title.length}/100</p>
            </Field>
            
            <Field label="Description" hint="Include links and CTAs">
              <Textarea
                value={description}
                onChange={(e) => setDescription(e.target.value)}
                rows={6}
              />
            </Field>
            
            <div className="grid grid-cols-1 md:grid-cols-2 gap-4">
              <Field label="Tags" hint="Comma-separated">
                <Input
                  value={tags}
                  onChange={(e) => setTags(e.target.value)}
                  placeholder="tag1, tag2, tag3"
                />
              </Field>
              
              <Field label="Hashtags" hint="Space-separated">
                <Input
                  value={hashtags}
                  onChange={(e) => setHashtags(e.target.value)}
                  placeholder="#shorts #business"
                />
              </Field>
            </div>
            
            <Field label="Privacy">
              <Select value={privacy} onChange={(e) => setPrivacy(e.target.value as PrivacyStatus)}>
                <option value="private">Private</option>
                <option value="unlisted">Unlisted</option>
                <option value="public">Public</option>
              </Select>
            </Field>
          </Card>

          {/* Thumbnail */}
          <Card className="space-y-4">
            <h3 className="font-semibold">Thumbnail</h3>

            {/* Thumbnail Preview */}
            <div className="aspect-video bg-slate-100 rounded-lg overflow-hidden flex items-center justify-center">
              {video.thumbnail_url ? (
                <img
                  src={video.thumbnail_url}
                  alt="Video thumbnail"
                  className="w-full h-full object-cover"
                />
              ) : (
                <span className="text-slate-400 text-sm">No thumbnail generated</span>
              )}
            </div>

            {/* Thumbnail Prompt & Generate - directly below image */}
            <Field label="Thumbnail Prompt" hint="Describe the thumbnail you want AI to generate">
              <Textarea
                value={video.thumbnail_prompt || ""}
                onChange={(e) => {/* TODO: Add thumbnail prompt state */}}
                rows={2}
                placeholder="e.g., Professional business coaching scene with bold text overlay..."
              />
            </Field>
            <Button
              variant="secondary"
              className="w-full"
              disabled={isProcessing}
            >
              <Wand2 className="w-4 h-4" />
              Generate Thumbnail
            </Button>
          </Card>

          {/* Captions */}
          <Card className="space-y-4">
            <div className="flex items-center justify-between">
              <h3 className="font-semibold">Captions (SRT/Text)</h3>
              {video.captions && (
                <button
                  onClick={() => setCaptions(video.captions || "")}
                  className="text-xs text-slate-500 hover:text-slate-700"
                >
                  Reset to original
                </button>
              )}
            </div>

            {/* Language Selector for Translation - always visible */}
            <div className="border-b border-slate-200 pb-4">
              <p className="text-sm text-slate-600 mb-2">
                Generate captions in multiple languages for international audiences:
              </p>
              <LanguageSelector
                videoId={videoId}
                existingLanguages={getExistingCaptionLanguages(video)}
                onTranslationComplete={refresh}
                disabled={isProcessing || !captions}
              />
              {!captions && (
                <p className="text-xs text-slate-400 mt-2">
                  Request captions first to enable translation
                </p>
              )}
            </div>

            <Textarea
              value={captions}
              onChange={(e) => setCaptions(e.target.value)}
              rows={10}
              className="font-mono text-sm"
              placeholder="Captions will appear here after transcription..."
            />
          </Card>

          {/* Publish */}
          <Card className="flex items-center justify-between">
            <div>
              <h3 className="font-semibold">Publish to YouTube</h3>
              <p className="text-sm text-slate-600">
                {isPublished ? "Already published" : "Ready to publish when you are"}
              </p>
            </div>
            <Button
              onClick={handlePublish}
              busy={busy === "publish"}
              disabled={!ytConnected || isProcessing || isPublished}
            >
              <Youtube className="w-4 h-4" />
              {isPublished ? "Published" : "Publish"}
            </Button>
          </Card>
        </div>
      </div>
    </div>
  );
}
