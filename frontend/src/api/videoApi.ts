import axios, { AxiosError } from "axios";
import type {
  Video,
  CaptionResponse,
  MetadataResponse,
  PublishRequest,
  PublishResponse,
  YouTubeAccount,
  ConfidentialityResult
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "/api";

// Get or set user ID
function getUserId(): string {
  let userId = localStorage.getItem("vs_user_id");
  if (!userId) {
    userId = `user_${Math.random().toString(36).substring(2, 15)}`;
    localStorage.setItem("vs_user_id", userId);
  }
  return userId;
}

export function setUserId(userId: string) {
  localStorage.setItem("vs_user_id", userId);
}

// Create axios instance
export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 120_000
});

// Add auth header to all requests
api.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-User-Id"] = getUserId();
  return config;
});

// Error helper
export function prettyError(err: unknown): string {
  if (axios.isAxiosError(err)) {
    const ae = err as AxiosError<any>;
    const msg =
      ae.response?.data?.detail ||
      ae.response?.data?.message ||
      ae.response?.data ||
      ae.message;
    return typeof msg === "string" ? msg : JSON.stringify(msg);
  }
  return err instanceof Error ? err.message : String(err);
}

// ============================================
// VIDEO OPERATIONS
// ============================================

export async function listVideos(): Promise<Video[]> {
  const r = await api.get<Video[]>("/video");
  return r.data;
}

export async function getVideo(videoId: number): Promise<Video> {
  const r = await api.get<Video>(`/video/${videoId}`);
  return r.data;
}

export async function uploadVideo(
  file: File,
  onProgress?: (progress: number) => void
): Promise<Video> {
  const form = new FormData();
  form.append("file", file);

  const r = await api.post<Video>("/video/upload", form, {
    headers: { "Content-Type": "multipart/form-data" },
    onUploadProgress: (e) => {
      if (onProgress && e.total) {
        onProgress(Math.round((e.loaded * 100) / e.total));
      }
    }
  });
  return r.data;
}

export async function ingestFromUrl(videoUrl: string, filename?: string): Promise<Video> {
  const r = await api.post<Video>("/video/ingest", { video_url: videoUrl, filename });
  return r.data;
}

export async function updateVideo(videoId: number, patch: Partial<Video>): Promise<Video> {
  const r = await api.patch<Video>(`/video/${videoId}`, patch);
  return r.data;
}

export async function deleteVideo(videoId: number): Promise<void> {
  await api.delete(`/video/${videoId}`);
}

// ============================================
// CAPTIONS & AI
// ============================================

export async function requestCaptions(videoId: number, languageCode?: string): Promise<CaptionResponse> {
  const r = await api.post<CaptionResponse>("/video/caption", {
    video_id: videoId,
    language_code: languageCode || "en"
  });
  return r.data;
}

export async function generateMetadata(videoId: number): Promise<MetadataResponse> {
  const r = await api.post<MetadataResponse>("/video/metadata/generate", {
    video_id: videoId
  });
  return r.data;
}

export async function checkConfidentiality(videoId: number): Promise<ConfidentialityResult> {
  const r = await api.post<ConfidentialityResult>("/video/confidentiality/check", {
    video_id: videoId
  });
  return r.data;
}

// ============================================
// YOUTUBE
// ============================================

export async function getYouTubeStatus(): Promise<{ connected: boolean; account?: YouTubeAccount }> {
  const r = await api.get<{ connected: boolean; account?: YouTubeAccount }>("/youtube/status");
  return r.data;
}

export async function startYouTubeOAuth(): Promise<{ auth_url: string }> {
  const r = await api.post<{ auth_url: string }>("/youtube/auth/start");
  return r.data;
}

export async function exchangeYouTubeCode(code: string, state: string): Promise<{ ok: boolean }> {
  const r = await api.post<{ ok: boolean }>("/youtube/auth/callback", { code, state });
  return r.data;
}

export async function publishToYouTube(payload: PublishRequest): Promise<PublishResponse> {
  const r = await api.post<PublishResponse>("/youtube/publish", payload);
  return r.data;
}

export async function disconnectYouTube(): Promise<void> {
  await api.delete("/youtube/disconnect");
}
