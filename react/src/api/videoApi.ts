import axios, { AxiosError } from "axios";
import type {
  Video,
  CaptionResponse,
  GenerateMetadataRequest,
  GenerateMetadataResponse,
  PublishRequest,
  PublishResponse,
  YouTubeAccount
} from "../types";

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL || "http://localhost:8080";

function getUserId(): string {
  return localStorage.getItem("vs_user_id") || "demo-user";
}

export const api = axios.create({
  baseURL: API_BASE_URL,
  timeout: 60_000
});

api.interceptors.request.use((config) => {
  config.headers = config.headers || {};
  config.headers["X-User-Id"] = getUserId();
  return config;
});

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

// ---- Videos ----

export async function listVideos(): Promise<Video[]> {
  // expected backend: GET /video
  // fallback: GET /video/list
  try {
    const r = await api.get<Video[]>("/video");
    return r.data;
  } catch {
    const r = await api.get<Video[]>("/video/list");
    return r.data;
  }
}

export async function getVideo(videoId: number): Promise<Video> {
  const r = await api.get<Video>(`/video/${videoId}`);
  return r.data;
}

export async function uploadVideo(file: File): Promise<Video> {
  const form = new FormData();
  form.append("file", file);

  const r = await api.post<any>("/video/upload", form, {
    headers: { "Content-Type": "multipart/form-data" }
  });

  // tolerate different shapes
  const data = r.data;
  const id = data?.id ?? data?.video_id ?? data?.video?.id;
  if (id) return getVideo(Number(id));

  // if backend returns full video object already:
  if (data?.storage_path && data?.original_filename) return data as Video;

  throw new Error("Upload succeeded but backend did not return a video id.");
}

export async function ingestFromUrl(videoUrl: string, filename?: string): Promise<Video> {
  // optional helper if you support “existing sitting file”
  const r = await api.post<any>("/video/ingest", {
    video_url: videoUrl,
    filename
  });

  const id = r.data?.id ?? r.data?.video_id ?? r.data?.video?.id;
  if (id) return getVideo(Number(id));
  if (r.data?.storage_path) return r.data as Video;

  throw new Error("Ingest succeeded but backend did not return a video id.");
}

export async function updateVideoMetadata(videoId: number, patch: Partial<Video>): Promise<Video> {
  const r = await api.patch<any>(`/video/${videoId}`, patch);
  // tolerate shapes
  const id = r.data?.id ?? r.data?.video_id ?? videoId;
  return getVideo(Number(id));
}

// ---- Captions (calls backend which calls n8n form-encoded) ----

export async function requestCaptions(videoId: number): Promise<CaptionResponse> {
  // expected backend: POST /video/caption { video_id }
  const r = await api.post<CaptionResponse>("/video/caption", { video_id: videoId });
  return r.data;
}

export async function saveCaptions(videoId: number, captions: string, transcript?: string): Promise<Video> {
  return updateVideoMetadata(videoId, {
    captions,
    transcript: transcript ?? undefined,
    status: "metadata_ready"
  });
}

// ---- AI metadata (optional; if backend has it) ----

export async function generateMetadata(req: GenerateMetadataRequest): Promise<GenerateMetadataResponse> {
  // expected backend: POST /video/metadata/generate
  const r = await api.post<GenerateMetadataResponse>("/video/metadata/generate", req);
  return r.data;
}

// ---- YouTube OAuth ----

export async function getYouTubeStatus(): Promise<{ connected: boolean; account?: YouTubeAccount }> {
  // expected backend: GET /youtube/status
  const r = await api.get<{ connected: boolean; account?: YouTubeAccount }>("/youtube/status");
  return r.data;
}

export async function startYouTubeOAuth(): Promise<{ auth_url: string }> {
  // expected backend: POST /youtube/auth/start => { auth_url }
  const r = await api.post<{ auth_url: string }>("/youtube/auth/start");
  return r.data;
}

export async function exchangeYouTubeCode(code: string, state?: string): Promise<{ ok: boolean }> {
  // expected backend: POST /youtube/auth/callback { code, state }
  const r = await api.post<{ ok: boolean }>("/youtube/auth/callback", { code, state });
  return r.data;
}

// ---- Publish ----

export async function publishToYouTube(payload: PublishRequest): Promise<PublishResponse> {
  // expected backend: POST /youtube/publish
  const r = await api.post<PublishResponse>("/youtube/publish", payload);
  return r.data;
}
