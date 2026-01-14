export type VideoStatus =
  | "uploading"
  | "ready"
  | "processing"
  | "captioning"
  | "metadata_ready"
  | "published"
  | "error";

export type PrivacyStatus = "private" | "unlisted" | "public";

export interface Video {
  id: number;
  user_id?: string;
  original_filename: string;
  storage_path: string;
  status: VideoStatus | string;
  transcript?: string | null;
  captions?: string | null; // store SRT text (preferred) or plain text
  duration_ms?: number | null;

  title?: string | null;
  description?: string | null;
  tags?: string | null;
  hashtags?: string | null;
  thumbnail_url?: string | null;

  language?: string | null;
  privacy_status?: PrivacyStatus | string;

  youtube_id?: string | null;
  youtube_url?: string | null;

  created_at?: string;
  updated_at?: string;
  error_message?: string | null;
}

export interface YouTubeAccount {
  platform: "youtube";
  account_id?: string;
  account_name?: string;
  channel_id?: string;
  profile_image_url?: string;
  is_active?: boolean;
}

export interface PublishRequest {
  video_id: number;
  title?: string;
  description?: string;
  tags?: string;
  privacy_status?: PrivacyStatus;
  thumbnail_url?: string;
}

export interface PublishResponse {
  youtube_id?: string;
  youtube_url?: string;
  status?: string;
}

export interface CaptionResponse {
  captions_format: "srt" | "text";
  captions: string;
}

export interface GenerateMetadataRequest {
  video_id: number;
  prompt?: string;
  model?: string;
  tone?: string;
  hashtags?: boolean;
}

export interface GenerateMetadataResponse {
  title?: string;
  description?: string;
  tags?: string;
  hashtags?: string;
}
