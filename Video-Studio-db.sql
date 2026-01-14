-- Required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- USERS
CREATE TABLE users (
    id UUID PRIMARY KEY DEFAULT gen_random_uuid(),
    email VARCHAR UNIQUE NOT NULL,
    first_name VARCHAR,
    last_name VARCHAR,
    profile_image_url TEXT,
    role VARCHAR DEFAULT 'user',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now()
);

-- USER SOCIAL MEDIA ACCOUNTS (e.g., YouTube, TikTok, IG, etc.)
CREATE TABLE user_social_accounts (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    platform TEXT NOT NULL, -- e.g. 'youtube', 'tiktok'
    account_id TEXT,
    account_name TEXT,
    channel_id TEXT,
    profile_image_url TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    is_active BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_user FOREIGN KEY (user_id) REFERENCES users(id)
);

-- CLOUD CONNECTIONS (Dropbox, OneDrive, GDrive)
CREATE TABLE cloud_connections (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    provider TEXT NOT NULL, -- dropbox, gdrive, onedrive
    account_email TEXT,
    selected_folder_path TEXT,
    is_active BOOLEAN DEFAULT true,
    last_synced_at TIMESTAMP,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP,
    metadata JSONB,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_user_cloud FOREIGN KEY (user_id) REFERENCES users(id)
);

-- VIDEOS (base video asset uploaded or selected)
CREATE TABLE videos (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    source_platform TEXT, -- e.g. 'dropbox', 'gdrive', 'upload'
    status TEXT DEFAULT 'uploading', -- uploading, ready, processing, published
    transcript TEXT,
    captions TEXT,
    duration_ms INTEGER,
    language TEXT DEFAULT 'en',
    error_message TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_user_video FOREIGN KEY (user_id) REFERENCES users(id)
);

-- VIDEO VERSIONS (clipped, trimmed, translated, etc.)
CREATE TABLE video_versions (
    id SERIAL PRIMARY KEY,
    video_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    version_name TEXT, -- e.g. "short clip", "spanish version"
    start_time_ms INTEGER,
    end_time_ms INTEGER,
    trimmed_file_path TEXT,
    speaker_image_url TEXT,
    sentiment TEXT,
    categories TEXT,
    hashtags TEXT,
    language TEXT DEFAULT 'en',
    confidentiality_status TEXT DEFAULT 'pending',
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_video_version FOREIGN KEY (video_id) REFERENCES videos(id),
    CONSTRAINT fk_user_version FOREIGN KEY (user_id) REFERENCES users(id)
);

-- GENERATED METADATA (title, description, tags)
CREATE TABLE video_metadata (
    id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL,
    title TEXT,
    description TEXT,
    tags TEXT,
    thumbnail_prompt TEXT,
    thumbnail_url TEXT,
    ai_generated BOOLEAN DEFAULT true,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_version_meta FOREIGN KEY (version_id) REFERENCES video_versions(id)
);

-- PUBLISH HISTORY PER PLATFORM
CREATE TABLE video_publish_events (
    id SERIAL PRIMARY KEY,
    version_id INTEGER NOT NULL,
    user_id UUID NOT NULL,
    platform TEXT NOT NULL, -- 'youtube', 'tiktok', 'instagram'
    publish_status TEXT DEFAULT 'pending', -- success, failed, scheduled
    privacy_status TEXT DEFAULT 'private',
    published_at TIMESTAMP,
    platform_video_id TEXT,
    platform_url TEXT,
    error_message TEXT,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_version_publish FOREIGN KEY (version_id) REFERENCES video_versions(id),
    CONSTRAINT fk_user_publish FOREIGN KEY (user_id) REFERENCES users(id)
);

-- INGEST REQUESTS
CREATE TABLE video_ingest_requests (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    video_id INTEGER,
    provider TEXT NOT NULL,
    source_path TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_file_size INTEGER,
    status TEXT DEFAULT 'queued', -- queued, downloading, processing, done
    progress JSONB,
    error_message TEXT,
    downloaded_path TEXT,
    started_at TIMESTAMP,
    completed_at TIMESTAMP,
    created_at TIMESTAMP DEFAULT now(),
    updated_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_ingest_user FOREIGN KEY (user_id) REFERENCES users(id),
    CONSTRAINT fk_ingest_video FOREIGN KEY (video_id) REFERENCES videos(id)
);

-- SEARCH LOG (optional)
CREATE TABLE video_search_queries (
    id SERIAL PRIMARY KEY,
    user_id UUID NOT NULL,
    query TEXT NOT NULL,
    results JSONB,
    total_found INTEGER DEFAULT 0,
    created_at TIMESTAMP DEFAULT now(),
    CONSTRAINT fk_search_user FOREIGN KEY (user_id) REFERENCES users(id)
);

CREATE INDEX idx_videos_user ON videos(user_id);
CREATE INDEX idx_versions_video ON video_versions(video_id);
CREATE INDEX idx_publish_version ON video_publish_events(version_id);
CREATE INDEX idx_metadata_version ON video_metadata(version_id);

