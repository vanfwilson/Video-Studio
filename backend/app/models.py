from sqlalchemy import Column, Integer, String, Text, Boolean, BigInteger, DateTime, ForeignKey
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.sql import func
from app.db import Base

class User(Base):
    __tablename__ = "users"
    
    id = Column(String(255), primary_key=True)
    email = Column(String(255), unique=True, nullable=True)
    first_name = Column(String(255), nullable=True)
    last_name = Column(String(255), nullable=True)
    profile_image_url = Column(Text, nullable=True)
    role = Column(String(50), default="user")
    default_channel_id = Column(String(255), nullable=True)
    notes = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class UserSocialAccount(Base):
    __tablename__ = "user_social_accounts"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    platform = Column(String(50), default="youtube")
    account_id = Column(String(255), nullable=True)
    account_name = Column(String(255), nullable=True)
    account_email = Column(String(255), nullable=True)
    channel_id = Column(String(255), nullable=True)
    profile_image_url = Column(Text, nullable=True)
    access_token = Column(Text, nullable=True)
    refresh_token = Column(Text, nullable=True)
    token_expires_at = Column(DateTime(timezone=True), nullable=True)
    is_active = Column(Boolean, default=True)
    metadata = Column(JSONB, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class OAuthState(Base):
    __tablename__ = "oauth_states"
    
    id = Column(Integer, primary_key=True)
    provider = Column(String(50), nullable=False)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    state = Column(String(255), nullable=False, unique=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())


class Video(Base):
    __tablename__ = "videos"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    
    # File info
    original_filename = Column(Text, nullable=False)
    storage_path = Column(Text, nullable=False)
    file_size = Column(BigInteger, nullable=True)
    mime_type = Column(String(100), default="video/mp4")
    duration_ms = Column(Integer, nullable=True)
    
    # Status
    status = Column(String(50), default="uploading")
    error_message = Column(Text, nullable=True)
    
    # Transcription
    transcript = Column(Text, nullable=True)
    captions = Column(JSONB, nullable=True)
    language = Column(String(10), default="en")
    
    # AI Metadata
    ai_summary = Column(Text, nullable=True)
    title = Column(String(500), nullable=True)
    description = Column(Text, nullable=True)
    tags = Column(Text, nullable=True)
    hashtags = Column(Text, nullable=True)
    thumbnail_prompt = Column(Text, nullable=True)
    thumbnail_url = Column(Text, nullable=True)
    
    # Publishing
    privacy_status = Column(String(20), default="private")
    category = Column(String(50), default="22")
    
    # YouTube
    youtube_id = Column(String(100), nullable=True)
    youtube_url = Column(Text, nullable=True)
    youtube_channel_id = Column(String(100), nullable=True)
    youtube_response = Column(JSONB, nullable=True)
    published_at = Column(DateTime(timezone=True), nullable=True)
    
    # Confidentiality
    confidentiality_status = Column(String(50), default="pending")
    confidentiality_issues = Column(JSONB, default=[])
    last_confidentiality_check_at = Column(DateTime(timezone=True), nullable=True)
    
    # Editing
    parent_video_id = Column(Integer, ForeignKey("videos.id"), nullable=True)
    trim_start_ms = Column(Integer, nullable=True)
    trim_end_ms = Column(Integer, nullable=True)
    speaker_image_url = Column(Text, nullable=True)
    sentiment = Column(Text, nullable=True)
    categories = Column(Text, nullable=True)
    
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class VideoIngestRequest(Base):
    __tablename__ = "video_ingest_requests"
    
    id = Column(Integer, primary_key=True)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="SET NULL"), nullable=True)
    provider = Column(String(50), nullable=False)
    source_path = Column(Text, nullable=False)
    source_file_name = Column(Text, nullable=False)
    source_file_size = Column(BigInteger, nullable=True)
    status = Column(String(50), default="queued")
    progress = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    downloaded_path = Column(Text, nullable=True)
    started_at = Column(DateTime(timezone=True), nullable=True)
    completed_at = Column(DateTime(timezone=True), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    updated_at = Column(DateTime(timezone=True), server_default=func.now(), onupdate=func.now())


class PublishTransaction(Base):
    __tablename__ = "publish_transactions"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), ForeignKey("users.id", ondelete="CASCADE"), nullable=False)
    action = Column(String(50), nullable=False)
    request_payload = Column(JSONB, nullable=False)
    status = Column(String(50), default="pending")
    response_payload = Column(JSONB, nullable=True)
    error_message = Column(Text, nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
    completed_at = Column(DateTime(timezone=True), nullable=True)


class ConfidentialityCheck(Base):
    __tablename__ = "confidentiality_checks"
    
    id = Column(Integer, primary_key=True)
    video_id = Column(Integer, ForeignKey("videos.id", ondelete="CASCADE"), nullable=False)
    user_id = Column(String(255), nullable=False)
    overall_status = Column(String(50), nullable=False)
    summary = Column(Text, nullable=True)
    counts = Column(JSONB, default={"high": 0, "medium": 0, "low": 0})
    segments = Column(JSONB, default=[])
    model_used = Column(String(255), nullable=True)
    created_at = Column(DateTime(timezone=True), server_default=func.now())
