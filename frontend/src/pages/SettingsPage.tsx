import React from "react";
import { Youtube, User, Key, Trash2, CheckCircle, XCircle, RefreshCw } from "lucide-react";
import {
  getYouTubeStatus,
  startYouTubeOAuth,
  disconnectYouTube,
  setUserId,
  prettyError
} from "../api/videoApi";
import { Button, Card, Field, Input, useToast } from "../components/ui";
import type { YouTubeAccount } from "../types";

export default function SettingsPage() {
  const toast = useToast();
  const [busy, setBusy] = React.useState<string | null>(null);

  // YouTube state
  const [ytConnected, setYtConnected] = React.useState(false);
  const [ytAccount, setYtAccount] = React.useState<YouTubeAccount | null>(null);

  // User ID state
  const [userId, setUserIdInput] = React.useState(() => {
    return localStorage.getItem("vs_user_id") || "";
  });

  const loadYouTubeStatus = async () => {
    try {
      const status = await getYouTubeStatus();
      setYtConnected(status.connected);
      setYtAccount(status.account || null);
    } catch (e) {
      console.error("Failed to load YouTube status:", e);
    }
  };

  React.useEffect(() => {
    loadYouTubeStatus();
  }, []);

  const handleConnectYouTube = async () => {
    setBusy("connect");
    try {
      const { auth_url } = await startYouTubeOAuth();
      window.location.href = auth_url;
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
      setBusy(null);
    }
  };

  const handleDisconnectYouTube = async () => {
    if (!confirm("Are you sure you want to disconnect your YouTube account?")) return;
    setBusy("disconnect");
    try {
      await disconnectYouTube();
      setYtConnected(false);
      setYtAccount(null);
      toast.push({ type: "success", message: "YouTube disconnected" });
    } catch (e) {
      toast.push({ type: "error", message: prettyError(e) });
    } finally {
      setBusy(null);
    }
  };

  const handleUpdateUserId = () => {
    if (!userId.trim()) {
      toast.push({ type: "error", message: "User ID cannot be empty" });
      return;
    }
    setUserId(userId.trim());
    toast.push({ type: "success", message: "User ID updated. Page will reload." });
    setTimeout(() => window.location.reload(), 1000);
  };

  const handleGenerateUserId = () => {
    const newId = `user_${Math.random().toString(36).substring(2, 15)}`;
    setUserIdInput(newId);
  };

  return (
    <div className="space-y-6">
      <div>
        <h1 className="text-2xl font-bold text-slate-900">Settings</h1>
        <p className="text-slate-600">Manage your connections and preferences</p>
      </div>

      <div className="grid grid-cols-1 lg:grid-cols-2 gap-6">
        {/* YouTube Connection */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Youtube className="w-5 h-5 text-red-600" />
            <h2 className="text-lg font-semibold">YouTube Connection</h2>
          </div>

          {ytConnected ? (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-green-50 rounded-lg">
                <CheckCircle className="w-5 h-5 text-green-600" />
                <div className="flex-1">
                  <p className="font-medium text-green-800">Connected</p>
                  <p className="text-sm text-green-700">
                    {ytAccount?.account_name || "YouTube Account"}
                  </p>
                  {ytAccount?.channel_id && (
                    <p className="text-xs text-green-600">
                      Channel: {ytAccount.channel_id}
                    </p>
                  )}
                </div>
                {ytAccount?.profile_image_url && (
                  <img
                    src={ytAccount.profile_image_url}
                    alt="Profile"
                    className="w-10 h-10 rounded-full"
                  />
                )}
              </div>

              <div className="flex gap-2">
                <Button
                  variant="secondary"
                  onClick={handleConnectYouTube}
                  busy={busy === "connect"}
                  className="flex-1"
                >
                  <RefreshCw className="w-4 h-4" />
                  Reconnect
                </Button>
                <Button
                  variant="secondary"
                  onClick={handleDisconnectYouTube}
                  busy={busy === "disconnect"}
                  className="text-red-600 hover:text-red-700"
                >
                  <Trash2 className="w-4 h-4" />
                  Disconnect
                </Button>
              </div>
            </div>
          ) : (
            <div className="space-y-4">
              <div className="flex items-center gap-3 p-3 bg-slate-50 rounded-lg">
                <XCircle className="w-5 h-5 text-slate-400" />
                <div>
                  <p className="font-medium text-slate-700">Not Connected</p>
                  <p className="text-sm text-slate-500">
                    Connect your YouTube channel to publish videos
                  </p>
                </div>
              </div>

              <Button
                onClick={handleConnectYouTube}
                busy={busy === "connect"}
                className="w-full"
              >
                <Youtube className="w-4 h-4" />
                Connect YouTube
              </Button>
            </div>
          )}

          <p className="text-xs text-slate-500">
            Video Studio uses OAuth to securely connect to your YouTube channel.
            We never store your password.
          </p>
        </Card>

        {/* User Identity */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <User className="w-5 h-5 text-primary-600" />
            <h2 className="text-lg font-semibold">User Identity</h2>
          </div>

          <p className="text-sm text-slate-600">
            Your videos and settings are linked to this User ID. Changing it
            will switch to a different user's data.
          </p>

          <Field label="User ID" hint="Unique identifier for your account">
            <div className="flex gap-2">
              <Input
                value={userId}
                onChange={(e) => setUserIdInput(e.target.value)}
                placeholder="user_xxx..."
                className="font-mono text-sm"
              />
              <Button
                variant="secondary"
                onClick={handleGenerateUserId}
                title="Generate random ID"
              >
                <Key className="w-4 h-4" />
              </Button>
            </div>
          </Field>

          <Button variant="secondary" onClick={handleUpdateUserId}>
            Update User ID
          </Button>

          <div className="p-3 bg-amber-50 rounded-lg">
            <p className="text-xs text-amber-700">
              <strong>Note:</strong> In production, integrate with your
              authentication provider (Clerk, Auth0, etc.) to automatically
              set the User ID.
            </p>
          </div>
        </Card>

        {/* API Configuration */}
        <Card className="space-y-4">
          <div className="flex items-center gap-2">
            <Key className="w-5 h-5 text-slate-600" />
            <h2 className="text-lg font-semibold">API Configuration</h2>
          </div>

          <div className="space-y-2 text-sm">
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-600">API Base URL</span>
              <span className="font-mono text-slate-900">
                {import.meta.env.VITE_API_BASE_URL || "/api"}
              </span>
            </div>
            <div className="flex justify-between py-2 border-b border-slate-100">
              <span className="text-slate-600">User ID Header</span>
              <span className="font-mono text-slate-900">X-User-Id</span>
            </div>
          </div>

          <p className="text-xs text-slate-500">
            API configuration is set during build time. Update environment
            variables and rebuild to change.
          </p>
        </Card>

        {/* About */}
        <Card className="space-y-4">
          <h2 className="text-lg font-semibold">About Video Studio</h2>

          <div className="space-y-2 text-sm text-slate-600">
            <p>
              Video Studio streamlines the process of publishing video clips
              to YouTube with AI-powered transcription, metadata generation,
              and confidentiality checking.
            </p>
            <p>
              Built for content creators who want to publish faster without
              sacrificing quality or security.
            </p>
          </div>

          <div className="pt-2 border-t border-slate-100">
            <div className="flex justify-between text-sm">
              <span className="text-slate-500">Version</span>
              <span className="font-mono text-slate-700">1.0.0</span>
            </div>
          </div>
        </Card>
      </div>
    </div>
  );
}
