-- Video Studio Database Schema
-- PostgreSQL 16 with extensions

-- Required extensions
CREATE EXTENSION IF NOT EXISTS "pgcrypto";
CREATE EXTENSION IF NOT EXISTS "uuid-ossp";

-- ===========================================
-- USERS
-- ===========================================
CREATE TABLE IF NOT EXISTS users (
    id VARCHAR(255) PRIMARY KEY,  -- External ID (Clerk, WP, etc)
    email VARCHAR(255) UNIQUE,
    first_name VARCHAR(255),
    last_name VARCHAR(255),
    profile_image_url TEXT,
    role VARCHAR(50) DEFAULT 'user',
    default_channel_id VARCHAR(255),
    notes TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- YOUTUBE/SOCIAL ACCOUNTS (per-user OAuth)
-- ===========================================
CREATE TABLE IF NOT EXISTS user_social_accounts (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    platform VARCHAR(50) NOT NULL DEFAULT 'youtube',
    account_id VARCHAR(255),
    account_name VARCHAR(255),
    account_email VARCHAR(255),
    channel_id VARCHAR(255),
    profile_image_url TEXT,
    access_token TEXT,
    refresh_token TEXT,
    token_expires_at TIMESTAMP WITH TIME ZONE,
    is_active BOOLEAN DEFAULT TRUE,
    metadata JSONB,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- OAUTH STATES (CSRF protection)
-- ===========================================
CREATE TABLE IF NOT EXISTS oauth_states (
    id SERIAL PRIMARY KEY,
    provider VARCHAR(50) NOT NULL,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    state VARCHAR(255) NOT NULL UNIQUE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- VIDEOS (main video records)
-- ===========================================
CREATE TABLE IF NOT EXISTS videos (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    
    -- File info
    original_filename TEXT NOT NULL,
    storage_path TEXT NOT NULL,
    file_size BIGINT,
    mime_type VARCHAR(100) DEFAULT 'video/mp4',
    duration_ms INTEGER,
    
    -- Processing status
    status VARCHAR(50) DEFAULT 'uploading' CHECK (status IN (
        'uploading', 'ready', 'captioning', 'metadata_ready', 
        'publishing', 'published', 'error'
    )),
    error_message TEXT,
    
    -- Transcription
    transcript TEXT,
    captions JSONB,  -- {format: "srt"|"text", srt: "...", text: "..."}
    language VARCHAR(10) DEFAULT 'en',
    
    -- AI-generated metadata
    ai_summary TEXT,
    title VARCHAR(500),
    description TEXT,
    tags TEXT,
    hashtags TEXT,
    thumbnail_prompt TEXT,
    thumbnail_url TEXT,
    
    -- Privacy & Publishing
    privacy_status VARCHAR(20) DEFAULT 'private' CHECK (privacy_status IN ('private', 'unlisted', 'public')),
    category VARCHAR(50) DEFAULT '22',
    
    -- YouTube info
    youtube_id VARCHAR(100),
    youtube_url TEXT,
    youtube_channel_id VARCHAR(100),
    youtube_response JSONB,
    published_at TIMESTAMP WITH TIME ZONE,
    
    -- Confidentiality
    confidentiality_status VARCHAR(50) DEFAULT 'pending' CHECK (confidentiality_status IN ('pending', 'pass', 'warn', 'fail')),
    confidentiality_issues JSONB DEFAULT '[]'::jsonb,
    last_confidentiality_check_at TIMESTAMP WITH TIME ZONE,
    
    -- Video editing (for future clip support)
    parent_video_id INTEGER REFERENCES videos(id),
    trim_start_ms INTEGER,
    trim_end_ms INTEGER,
    speaker_image_url TEXT,
    sentiment TEXT,
    categories TEXT,
    
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- VIDEO INGEST REQUESTS (for cloud imports)
-- ===========================================
CREATE TABLE IF NOT EXISTS video_ingest_requests (
    id SERIAL PRIMARY KEY,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    video_id INTEGER REFERENCES videos(id) ON DELETE SET NULL,
    provider VARCHAR(50) NOT NULL,
    source_path TEXT NOT NULL,
    source_file_name TEXT NOT NULL,
    source_file_size BIGINT,
    status VARCHAR(50) DEFAULT 'queued' CHECK (status IN ('queued', 'downloading', 'processing', 'done', 'error')),
    progress JSONB,
    error_message TEXT,
    downloaded_path TEXT,
    started_at TIMESTAMP WITH TIME ZONE,
    completed_at TIMESTAMP WITH TIME ZONE,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    updated_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- PUBLISH TRANSACTIONS (audit trail)
-- ===========================================
CREATE TABLE IF NOT EXISTS publish_transactions (
    id SERIAL PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL REFERENCES users(id) ON DELETE CASCADE,
    action VARCHAR(50) NOT NULL CHECK (action IN ('transcribe', 'metadata', 'confidentiality', 'publish')),
    request_payload JSONB NOT NULL,
    status VARCHAR(50) DEFAULT 'pending' CHECK (status IN ('pending', 'success', 'failed')),
    response_payload JSONB,
    error_message TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW(),
    completed_at TIMESTAMP WITH TIME ZONE
);

-- ===========================================
-- CONFIDENTIALITY CHECK RECORDS
-- ===========================================
CREATE TABLE IF NOT EXISTS confidentiality_checks (
    id SERIAL PRIMARY KEY,
    video_id INTEGER NOT NULL REFERENCES videos(id) ON DELETE CASCADE,
    user_id VARCHAR(255) NOT NULL,
    overall_status VARCHAR(50) NOT NULL,
    summary TEXT,
    counts JSONB DEFAULT '{"high": 0, "medium": 0, "low": 0}'::jsonb,
    segments JSONB DEFAULT '[]'::jsonb,
    model_used VARCHAR(255),
    created_at TIMESTAMP WITH TIME ZONE DEFAULT NOW()
);

-- ===========================================
-- INDEXES
-- ===========================================
CREATE INDEX IF NOT EXISTS idx_users_email ON users(email);
CREATE INDEX IF NOT EXISTS idx_videos_user_id ON videos(user_id);
CREATE INDEX IF NOT EXISTS idx_videos_status ON videos(status);
CREATE INDEX IF NOT EXISTS idx_videos_created_at ON videos(created_at DESC);
CREATE INDEX IF NOT EXISTS idx_social_accounts_user ON user_social_accounts(user_id, platform);
CREATE INDEX IF NOT EXISTS idx_oauth_states_state ON oauth_states(state);
CREATE INDEX IF NOT EXISTS idx_ingest_user ON video_ingest_requests(user_id);
CREATE INDEX IF NOT EXISTS idx_transactions_video ON publish_transactions(video_id);
CREATE INDEX IF NOT EXISTS idx_confidentiality_video ON confidentiality_checks(video_id);

-- ===========================================
-- TRIGGERS for updated_at
-- ===========================================
CREATE OR REPLACE FUNCTION update_updated_at_column()
RETURNS TRIGGER AS $$
BEGIN
    NEW.updated_at = NOW();
    RETURN NEW;
END;
$$ LANGUAGE plpgsql;

DROP TRIGGER IF EXISTS update_users_updated_at ON users;
CREATE TRIGGER update_users_updated_at
    BEFORE UPDATE ON users
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_videos_updated_at ON videos;
CREATE TRIGGER update_videos_updated_at
    BEFORE UPDATE ON videos
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_social_accounts_updated_at ON user_social_accounts;
CREATE TRIGGER update_social_accounts_updated_at
    BEFORE UPDATE ON user_social_accounts
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

DROP TRIGGER IF EXISTS update_ingest_updated_at ON video_ingest_requests;
CREATE TRIGGER update_ingest_updated_at
    BEFORE UPDATE ON video_ingest_requests
    FOR EACH ROW EXECUTE FUNCTION update_updated_at_column();

-- ===========================================
-- PERMISSIONS
-- ===========================================
GRANT ALL PRIVILEGES ON ALL TABLES IN SCHEMA public TO video_studio;
GRANT ALL PRIVILEGES ON ALL SEQUENCES IN SCHEMA public TO video_studio;
