import React from "react";
import { useNavigate } from "react-router-dom";
import { Upload, FileVideo, X, CheckCircle } from "lucide-react";
import { uploadVideo, ingestFromUrl, prettyError } from "../api/videoApi";
import { Button, Card, Field, Input, useToast } from "../components/ui";

export default function UploadPage() {
  const toast = useToast();
  const navigate = useNavigate();
  
  const [busy, setBusy] = React.useState(false);
  const [file, setFile] = React.useState<File | null>(null);
  const [progress, setProgress] = React.useState(0);
  const [uploadedId, setUploadedId] = React.useState<number | null>(null);
  
  // Ingest form
  const [url, setUrl] = React.useState("");
  const [filename, setFilename] = React.useState("");
  
  const [dragActive, setDragActive] = React.useState(false);

  const handleDrag = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    if (e.type === "dragenter" || e.type === "dragover") {
      setDragActive(true);
    } else if (e.type === "dragleave") {
      setDragActive(false);
    }
  };

  const handleDrop = (e: React.DragEvent) => {
    e.preventDefault();
    e.stopPropagation();
    setDragActive(false);
    if (e.dataTransfer.files && e.dataTransfer.files[0]) {
      handleFileSelect(e.dataTransfer.files[0]);
    }
  };

  const handleFileSelect = (f: File) => {
    const allowed = ["video/mp4", "video/quicktime", "video/webm", "video/x-matroska", "video/x-msvideo"];
    if (!allowed.includes(f.type)) {
      toast.push({ type: "error", message: "Please select a valid video file (MP4, MOV, WebM, MKV, AVI)" });
      return;
    }
    setFile(f);
    setProgress(0);
    setUploadedId(null);
  };

  const handleUpload = async () => {
    if (!file) return;
    setBusy(true);
    try {
      const video = await uploadVideo(file, setProgress);
      setUploadedId(video.id);
      toast.push({ type: "success", message: "Upload complete!" });
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  const handleIngest = async () => {
    if (!url.trim()) return;
    setBusy(true);
    try {
      const video = await ingestFromUrl(url.trim(), filename.trim() || undefined);
      toast.push({ type: "success", message: "Video ingested!" });
      navigate(`/video/${video.id}`);
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(false);
    }
  };

  const handleClear = () => {
    setFile(null);
    setProgress(0);
    setUploadedId(null);
  };

  const formatSize = (bytes: number) => {
    const mb = bytes / 1024 / 1024;
    return mb > 1 ? `${mb.toFixed(1)} MB` : `${(bytes / 1024).toFixed(1)} KB`;
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Upload Video</h1>
        <p className="text-slate-600">
          Upload a file directly or ingest from a public URL
        </p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* Direct Upload */}
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold">Direct Upload</h2>

          {!file ? (
            <div
              className={`border-2 border-dashed rounded-xl p-8 text-center transition-colors ${
                dragActive ? "border-primary-500 bg-primary-50" : "border-slate-300"
              }`}
              onDragEnter={handleDrag}
              onDragLeave={handleDrag}
              onDragOver={handleDrag}
              onDrop={handleDrop}
            >
              <Upload className="w-10 h-10 text-slate-400 mx-auto mb-3" />
              <p className="text-slate-700 font-medium mb-1">
                Drag and drop your video here
              </p>
              <p className="text-sm text-slate-500 mb-3">or click to browse</p>
              <input
                type="file"
                accept="video/*"
                onChange={(e) => e.target.files?.[0] && handleFileSelect(e.target.files[0])}
                className="hidden"
                id="file-input"
              />
              <label htmlFor="file-input" className="inline-flex items-center justify-center gap-2 px-4 py-2 rounded-lg font-medium text-sm transition-colors bg-slate-100 text-slate-700 hover:bg-slate-200 border border-slate-200 cursor-pointer">
                Select File
              </label>
              <p className="text-xs text-slate-400 mt-3">
                MP4, MOV, WebM, MKV, AVI up to 2GB
              </p>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-start gap-3 p-3 bg-slate-50 rounded-lg">
                <FileVideo className="w-10 h-10 text-slate-400 flex-shrink-0" />
                <div className="flex-1 min-w-0">
                  <p className="font-medium text-slate-900 truncate">{file.name}</p>
                  <p className="text-sm text-slate-500">{formatSize(file.size)}</p>
                  
                  {busy && (
                    <div className="mt-2">
                      <div className="flex justify-between text-sm text-slate-600 mb-1">
                        <span>Uploading...</span>
                        <span>{progress}%</span>
                      </div>
                      <div className="w-full bg-slate-200 rounded-full h-2">
                        <div
                          className="bg-primary-600 h-2 rounded-full transition-all"
                          style={{ width: `${progress}%` }}
                        />
                      </div>
                    </div>
                  )}
                  
                  {uploadedId && (
                    <div className="mt-2 flex items-center gap-2 text-green-600">
                      <CheckCircle className="w-4 h-4" />
                      <span className="text-sm">Upload complete!</span>
                    </div>
                  )}
                </div>
                {!busy && !uploadedId && (
                  <button
                    onClick={handleClear}
                    className="text-slate-400 hover:text-slate-600"
                  >
                    <X className="w-5 h-5" />
                  </button>
                )}
              </div>

              <div className="flex gap-2">
                {!uploadedId ? (
                  <>
                    <Button onClick={handleUpload} busy={busy} className="flex-1">
                      Upload
                    </Button>
                    <Button variant="secondary" onClick={handleClear} disabled={busy}>
                      Cancel
                    </Button>
                  </>
                ) : (
                  <>
                    <Button onClick={() => navigate(`/video/${uploadedId}`)} className="flex-1">
                      Edit & Publish
                    </Button>
                    <Button variant="secondary" onClick={handleClear}>
                      Upload Another
                    </Button>
                  </>
                )}
              </div>
            </div>
          )}
        </Card>

        {/* URL Ingest */}
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold">Ingest from URL</h2>
          <p className="text-sm text-slate-600">
            Import a video from a public URL (cloud storage, CDN, etc.)
          </p>

          <Field label="Video URL" hint="Must be publicly accessible">
            <Input
              type="url"
              value={url}
              onChange={(e) => setUrl(e.target.value)}
              placeholder="https://example.com/video.mp4"
            />
          </Field>

          <Field label="Filename (optional)" hint="Helps identify the video">
            <Input
              value={filename}
              onChange={(e) => setFilename(e.target.value)}
              placeholder="my-video.mp4"
            />
          </Field>

          <Button
            variant="secondary"
            onClick={handleIngest}
            busy={busy}
            disabled={!url.trim()}
          >
            Ingest Video
          </Button>
        </Card>
      </div>

      {/* Process Overview */}
      <Card>
        <h3 className="font-semibold text-slate-900 mb-3">What happens next?</h3>
        <ol className="list-decimal list-inside text-sm text-slate-600 space-y-1">
          <li>Video is uploaded and stored</li>
          <li>Request AI transcription (captions + transcript)</li>
          <li>Generate metadata (title, description, tags) with AI</li>
          <li>Run confidentiality check for sensitive information</li>
          <li>Review, edit, and publish to YouTube</li>
        </ol>
      </Card>
    </div>
  );
}
