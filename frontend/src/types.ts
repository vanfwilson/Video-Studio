export type Video = {
  id: string | number;
  user_id: string;
  original_filename: string;
  storage_path: string;
  status: string;

  transcript?: string | null;
  captions?: string | null;

  ai_summary?: string | null;
  title?: string | null;
  description?: string | null;
  tags?: string | null;
  hashtags?: string | null;
  thumbnail_prompt?: string | null;
  thumbnail_url?: string | null;

  confidentiality_status?: string | null;

  youtube_id?: string | null;
  youtube_url?: string | null;

  error_message?: string | null;
};

export type ConfidentialityResult = {
  overall_status: "pass" | "warn" | "fail" | string;
  summary?: string;
  counts?: { high: number; medium: number; low: number };
  segments?: Array<{ risk: string; reason: string; snippet: string }>;
  model_used?: string;
  check_id?: string;
};
