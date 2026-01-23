export type VideoStatus =
  | "uploading"
  | "ready"
  | "captioning"
  | "metadata_ready"
  | "publishing"
  | "published"
  | "error";

export type PrivacyStatus = "private" | "unlisted" | "public";

export type ConfidentialityStatus = "pending" | "pass" | "warn" | "fail";

export interface Video {
  id: number;
  user_id: string;
  original_filename: string;
  storage_path: string;
  file_size?: number;
  mime_type?: string;
  duration_ms?: number;
  status: VideoStatus;
  error_message?: string;
  transcript?: string;
  captions?: string;
  language?: string;
  ai_summary?: string;
  title?: string;
  description?: string;
  tags?: string;
  hashtags?: string;
  thumbnail_prompt?: string;
  thumbnail_url?: string;
  privacy_status: PrivacyStatus;
  category?: string;
  youtube_id?: string;
  youtube_url?: string;
  youtube_channel_id?: string;
  published_at?: string;
  confidentiality_status: ConfidentialityStatus;
  confidentiality_issues?: ConfidentialitySegment[];
  created_at?: string;
  updated_at?: string;
}

export interface YouTubeAccount {
  platform: "youtube";
  account_id?: string;
  account_name?: string;
  channel_id?: string;
  profile_image_url?: string;
  is_active?: boolean;
}

export interface ConfidentialitySegment {
  risk: "high" | "medium" | "low";
  reason: string;
  snippet: string;
}

export interface ConfidentialityResult {
  overall_status: ConfidentialityStatus;
  summary: string;
  counts: { high: number; medium: number; low: number };
  segments: ConfidentialitySegment[];
  model_used?: string;
}

export interface CaptionResponse {
  captions_format: "srt" | "text";
  captions: string;
}

export interface MetadataResponse {
  ai_summary?: string;
  title?: string;
  description?: string;
  tags?: string;
  hashtags?: string;
  thumbnail_prompt?: string;
  model_used?: string;
}

export interface PublishRequest {
  video_id: number;
  title?: string;
  description?: string;
  tags?: string;
  privacy_status?: PrivacyStatus;
  category?: string;
}

export interface PublishResponse {
  ok: boolean;
  youtube_id?: string;
  youtube_url?: string;
  status?: string;
}
