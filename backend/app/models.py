from sqlalchemy import (
    Column, Integer, String, Text, Boolean, ForeignKey, DateTime, JSON
)
from sqlalchemy.dialects.postgresql import UUID, JSONB
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"
    id = Column(String, primary_key=True)  # store WP/Clerk user id as string (UUID/email/whatever)
    email = Column(String, unique=True, nullable=True)
    first_name = Column(String, nullable=True)
    last_name = Column(String, nullable=True)
    profile_image_url = Column(String, nullable=True)
    role = Column(String, nullable=True, default="user")
    default_channel_id = Column(String, nullable=True)
    notes = Column(String, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class CloudConnection(Base):
    __tablename__ = "cloud_connections"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(Text, nullable=False)
    account_id = Column(Text, nullable=True)
    account_name = Column(Text, nullable=True)
    account_email = Column(Text, nullable=True)
    profile_photo_url = Column(Text, nullable=True)
    selected_folder_path = Column(Text, nullable=True)
    selected_folder_name = Column(Text, nullable=True)
    is_active = Column(Text, nullable=True, default="true")
    last_synced_at = Column(DateTime, nullable=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class UserSocialAccount(Base):
    """
    Per-user platform connection (YouTube now; can extend to TikTok/IG/etc).
    Tokens should be encrypted at rest if APP_ENCRYPTION_KEY is set.
    """
    __tablename__ = "user_social_accounts"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    platform = Column(Text, nullable=False)  # 'youtube'
    account_id = Column(Text, nullable=True)
    account_name = Column(Text, nullable=True)
    account_email = Column(Text, nullable=True)
    channel_id = Column(Text, nullable=True)
    profile_image_url = Column(Text, nullable=True)

    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime, nullable=True)
    is_active = Column(Boolean, default=True)

    metadata = Column(JSONB, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class OAuthState(Base):
    __tablename__ = "oauth_states"
    id = Column(Integer, primary_key=True)
    provider = Column(Text, nullable=False)  # 'youtube'
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    state = Column(Text, nullable=False, unique=True)
    created_at = Column(DateTime, server_default=func.now())

class Video(Base):
    __tablename__ = "videos"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)

    original_filename = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)  # public URL or internal path; we also expose /uploads publicly
    status = Column(Text, nullable=False, default="uploading")

    # transcription
    transcript = Column(Text, nullable=True)
    captions = Column(JSONB, nullable=True)  # keep JSONB for compatibility (can also store SRT in JSONB as {srt:...})
    # metadata
    title = Column(Text, nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    thumbnail_prompt = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    language = Column(Text, nullable=True, default="en")
    privacy_status = Column(Text, nullable=True, default="private")

    # youtube
    youtube_id = Column(Text, nullable=True)
    youtube_url = Column(Text, nullable=True)

    # editing
    duration_ms = Column(Integer, nullable=True)
    suggested_start_ms = Column(Integer, nullable=True)
    trim_start_ms = Column(Integer, nullable=True)
    trim_end_ms = Column(Integer, nullable=True)
    parent_video_id = Column(Integer, nullable=True)
    start_sec = Column(Integer, nullable=True)
    end_sec = Column(Integer, nullable=True)

    # misc
    speaker_image_url = Column(Text, nullable=True)
    error_message = Column(Text, nullable=True)
    sentiment = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)
    confidentiality_status = Column(Text, nullable=True, default="pending")
    last_confidentiality_check_id = Column(Integer, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())

class VideoIngestRequest(Base):
    __tablename__ = "video_ingest_requests"
    id = Column(Integer, primary_key=True)
    user_id = Column(String, ForeignKey("users.id"), nullable=False)
    provider = Column(Text, nullable=False)
    source_path = Column(Text, nullable=False)
    source_file_name = Column(Text, nullable=False)
    source_file_size = Column(Integer, nullable=True)

    status = Column(Text, nullable=False, default="queued")
    progress = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)

    video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    downloaded_path = Column(Text, nullable=True)

    created_at = Column(DateTime, server_default=func.now())
    updated_at = Column(DateTime, server_default=func.now(), onupdate=func.now())
    started_at = Column(DateTime, nullable=True)
    completed_at = Column(DateTime, nullable=True)
