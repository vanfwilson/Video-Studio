from pydantic_settings import BaseSettings, SettingsConfigDict
from typing import Optional

class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Database
    DATABASE_URL: str = "postgresql://video_studio:video_studio@localhost:5432/video_studio"

    # Public URL for n8n to reach videos
    PUBLIC_BASE_URL: str = "http://localhost:8080"

    # n8n endpoints
    N8N_TRANSCRIBE_URL: str = "http://localhost:5678/webhook/transcribe"
    N8N_PUBLISH_URL: str = "http://localhost:5678/webhook/publish"
    DEFAULT_LANGUAGE_CODE: str = "en"

    # OpenRouter AI
    OPENROUTER_API_KEY: Optional[str] = None
    OPENROUTER_MODEL: str = "openai/gpt-4o-mini"
    OPENROUTER_SITE_URL: str = "https://video-studio.askstephen.ai"
    OPENROUTER_APP_NAME: str = "Video Studio"

    # YouTube OAuth
    YOUTUBE_CLIENT_ID: Optional[str] = None
    YOUTUBE_CLIENT_SECRET: Optional[str] = None
    YOUTUBE_REDIRECT_URI: Optional[str] = None
    YOUTUBE_SCOPES: str = "https://www.googleapis.com/auth/youtube.upload https://www.googleapis.com/auth/youtube.readonly"

    # Storage
    UPLOAD_DIR: str = "/data/uploads"
    MAX_UPLOAD_MB: int = 2000

    # CORS
    CORS_ORIGINS: str = "*"

    # Security
    APP_ENCRYPTION_KEY: Optional[str] = None

settings = Settings()
