from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision = "0001_init"
down_revision = None
branch_labels = None
depends_on = None

def upgrade():
    op.execute('CREATE EXTENSION IF NOT EXISTS "pgcrypto";')

    op.create_table(
        "users",
        sa.Column("id", sa.String(), primary_key=True),
        sa.Column("email", sa.String(), unique=True, nullable=True),
        sa.Column("first_name", sa.String(), nullable=True),
        sa.Column("last_name", sa.String(), nullable=True),
        sa.Column("profile_image_url", sa.Text(), nullable=True),
        sa.Column("role", sa.String(), nullable=True, server_default="user"),
        sa.Column("default_channel_id", sa.String(), nullable=True),
        sa.Column("notes", sa.String(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "oauth_states",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("state", sa.Text(), nullable=False, unique=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "user_social_accounts",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("platform", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Text(), nullable=True),
        sa.Column("account_name", sa.Text(), nullable=True),
        sa.Column("account_email", sa.Text(), nullable=True),
        sa.Column("channel_id", sa.Text(), nullable=True),
        sa.Column("profile_image_url", sa.Text(), nullable=True),
        sa.Column("access_token", sa.Text(), nullable=True),
        sa.Column("refresh_token", sa.Text(), nullable=True),
        sa.Column("token_expires_at", sa.DateTime(), nullable=True),
        sa.Column("is_active", sa.Boolean(), server_default=sa.text("true")),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "cloud_connections",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("account_id", sa.Text(), nullable=True),
        sa.Column("account_name", sa.Text(), nullable=True),
        sa.Column("account_email", sa.Text(), nullable=True),
        sa.Column("profile_photo_url", sa.Text(), nullable=True),
        sa.Column("selected_folder_path", sa.Text(), nullable=True),
        sa.Column("selected_folder_name", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Text(), server_default="true"),
        sa.Column("last_synced_at", sa.DateTime(), nullable=True),
        sa.Column("metadata", postgresql.JSONB(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "videos",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("original_filename", sa.Text(), nullable=False),
        sa.Column("storage_path", sa.Text(), nullable=False),
        sa.Column("status", sa.Text(), nullable=False, server_default="uploading"),

        sa.Column("transcript", sa.Text(), nullable=True),
        sa.Column("captions", postgresql.JSONB(), nullable=True),

        sa.Column("title", sa.Text(), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("tags", sa.Text(), nullable=True),
        sa.Column("hashtags", sa.Text(), nullable=True),
        sa.Column("thumbnail_prompt", sa.Text(), nullable=True),
        sa.Column("thumbnail_url", sa.Text(), nullable=True),

        sa.Column("language", sa.Text(), server_default="en"),
        sa.Column("privacy_status", sa.Text(), server_default="private"),

        sa.Column("youtube_id", sa.Text(), nullable=True),
        sa.Column("youtube_url", sa.Text(), nullable=True),

        sa.Column("duration_ms", sa.Integer(), nullable=True),
        sa.Column("suggested_start_ms", sa.Integer(), nullable=True),
        sa.Column("trim_start_ms", sa.Integer(), nullable=True),
        sa.Column("trim_end_ms", sa.Integer(), nullable=True),
        sa.Column("parent_video_id", sa.Integer(), nullable=True),
        sa.Column("start_sec", sa.Integer(), nullable=True),
        sa.Column("end_sec", sa.Integer(), nullable=True),

        sa.Column("speaker_image_url", sa.Text(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("sentiment", sa.Text(), nullable=True),
        sa.Column("categories", sa.Text(), nullable=True),
        sa.Column("confidentiality_status", sa.Text(), server_default="pending"),
        sa.Column("last_confidentiality_check_id", sa.Integer(), nullable=True),

        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
    )

    op.create_table(
        "video_ingest_requests",
        sa.Column("id", sa.Integer(), primary_key=True),
        sa.Column("user_id", sa.String(), sa.ForeignKey("users.id"), nullable=False),
        sa.Column("provider", sa.Text(), nullable=False),
        sa.Column("source_path", sa.Text(), nullable=False),
        sa.Column("source_file_name", sa.Text(), nullable=False),
        sa.Column("source_file_size", sa.Integer(), nullable=True),
        sa.Column("status", sa.Text(), nullable=False, server_default="queued"),
        sa.Column("progress", postgresql.JSONB(), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("video_id", sa.Integer(), sa.ForeignKey("videos.id"), nullable=True),
        sa.Column("downloaded_path", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("updated_at", sa.DateTime(), server_default=sa.text("now()")),
        sa.Column("started_at", sa.DateTime(), nullable=True),
        sa.Column("completed_at", sa.DateTime(), nullable=True),
    )

    op.create_index("idx_videos_user_id", "videos", ["user_id"])
    op.create_index("idx_ingest_user_id", "video_ingest_requests", ["user_id"])
    op.create_index("idx_social_user_platform", "user_social_accounts", ["user_id", "platform"])

def downgrade():
    op.drop_index("idx_social_user_platform", table_name="user_social_accounts")
    op.drop_index("idx_ingest_user_id", table_name="video_ingest_requests")
    op.drop_index("idx_videos_user_id", table_name="videos")
    op.drop_table("video_ingest_requests")
    op.drop_table("videos")
    op.drop_table("cloud_connections")
    op.drop_table("user_social_accounts")
    op.drop_table("oauth_states")
    op.drop_table("users")
