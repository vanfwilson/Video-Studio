from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import AnyHttpUrl
from typing import List, Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    DATABASE_URL: str

    # Public base URL that n8n can reach (used to build public video_url for /transcribe)
    PUBLIC_BASE_URL: str = "http://localhost:8088"

    # n8n endpoint
    N8N_TRANSCRIBE_URL: str = "http://72.60.225.136:8001/transcribe"
    DEFAULT_LANGUAGE_CODE: str = "en"

    # Upload storage
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_MB: int = 2000

    # CORS
    CORS_ORIGINS: str = "*"  # comma-separated or "*"

    # Token encryption (recommended)
    APP_ENCRYPTION_KEY: Optional[str] = None  # base64 key for Fernet

    # YouTube OAuth
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_REDIRECT_URI: Optional[str] = None  # e.g. https://video-studio.yourdomain.com/oauth/youtube/callback
    YOUTUBE_SCOPES: str = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"

settings = Settings()
