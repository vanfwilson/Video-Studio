#!/usr/bin/env python3
"""
YouTube Publisher - Complete video publishing with metadata, thumbnails, and captions.
Uses credentials stored in the askstephen database (video-studio app).

Usage:
    # Publish video with all metadata
    python youtube_publisher.py publish --video-id 8 --user-id "manual_xxx"

    # Upload captions only
    python youtube_publisher.py captions --youtube-id "VIDEO_ID" --file captions.srt --language es

    # Update metadata
    python youtube_publisher.py update --youtube-id "VIDEO_ID" --title "New Title"

    # List user's channels
    python youtube_publisher.py channels --user-id "manual_xxx"
"""

import os
import sys
import json
import time
import argparse
import tempfile
from typing import Optional
import psycopg2
from psycopg2.extras import RealDictCursor

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# Database configuration
DB_HOST = os.environ.get("DB_HOST", "localhost")
DB_PORT = os.environ.get("DB_PORT", "5432")
DB_NAME = os.environ.get("DB_NAME", "askstephen")
DB_USER = os.environ.get("DB_USER", "video_studio")
DB_PASSWORD = os.environ.get("DB_PASSWORD", "Masaya9989")

# YouTube OAuth client
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "10404446139-9tlvhjoicaf8ejsts4jaa1te761tsdvm.apps.googleusercontent.com")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "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")

# Upload settings
CHUNK_SIZE = 50 * 1024 * 1024  # 50MB chunks for resumable upload

# Video file location (docker volume)
VIDEO_UPLOADS_PATH = os.environ.get("VIDEO_UPLOADS_PATH",
    "/var/lib/docker/volumes/video-studio-test_video_test_uploads/_data")


def get_db_connection():
    """Get database connection."""
    # Try docker exec first, then direct connection
    try:
        return psycopg2.connect(
            host=DB_HOST,
            port=DB_PORT,
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )
    except:
        # If direct connection fails, we're probably running on the host
        # Use localhost which maps to docker host
        return psycopg2.connect(
            host="172.18.0.1",  # Docker bridge
            port="5432",
            database=DB_NAME,
            user=DB_USER,
            password=DB_PASSWORD
        )


def run_docker_sql(sql: str, fetch: bool = True):
    """Run SQL via docker exec (for host-to-container communication)."""
    import subprocess
    cmd = ["docker", "exec", "video-studio-db", "psql", "-U", DB_USER, "-d", DB_NAME, "-t", "-c", sql]
    result = subprocess.run(cmd, capture_output=True, text=True)
    if result.returncode != 0:
        raise Exception(f"SQL error: {result.stderr}")
    return result.stdout.strip() if fetch else None


def get_user_channels(user_id: str) -> list[dict]:
    """Get all YouTube channels for a user."""
    sql = f"""
        SELECT usa.id, usa.account_name, usa.channel_id, yc.name as channel_title
        FROM user_social_accounts usa
        LEFT JOIN youtube_channels yc ON yc.id = usa.channel_id
        WHERE usa.user_id = '{user_id}' AND usa.platform = 'youtube' AND usa.is_active = true
    """
    result = run_docker_sql(sql)
    channels = []
    for line in result.split('\n'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 4 and parts[0]:
            channels.append({
                "id": int(parts[0]),
                "account_name": parts[1],
                "channel_id": parts[2],
                "channel_title": parts[3]
            })
    return channels


def get_channel_credentials(user_id: str, channel_id: str = None) -> dict:
    """Get YouTube OAuth credentials for a user's channel."""
    if channel_id:
        sql = f"""
            SELECT access_token, refresh_token, metadata
            FROM user_social_accounts
            WHERE user_id = '{user_id}' AND platform = 'youtube'
            AND channel_id = '{channel_id}' AND is_active = true
        """
    else:
        # Get default channel
        sql = f"""
            SELECT usa.access_token, usa.refresh_token, usa.metadata
            FROM user_social_accounts usa
            JOIN users u ON u.id = usa.user_id
            WHERE usa.user_id = '{user_id}' AND usa.platform = 'youtube' AND usa.is_active = true
            AND (u.default_channel_id IS NULL OR usa.channel_id = u.default_channel_id)
            LIMIT 1
        """

    result = run_docker_sql(sql)
    if not result.strip():
        raise ValueError(f"No YouTube credentials found for user {user_id}" +
                        (f" channel {channel_id}" if channel_id else ""))

    parts = [p.strip() for p in result.split('|')]
    metadata = json.loads(parts[2]) if parts[2] else {}

    return {
        "access_token": parts[0],
        "refresh_token": parts[1],
        "client_id": metadata.get("client_id", YOUTUBE_CLIENT_ID)
    }


def build_youtube_service(creds_data: dict):
    """Build YouTube API service from credentials."""
    creds = Credentials(
        token=creds_data["access_token"],
        refresh_token=creds_data["refresh_token"],
        token_uri="https://oauth2.googleapis.com/token",
        client_id=creds_data.get("client_id", YOUTUBE_CLIENT_ID),
        client_secret=YOUTUBE_CLIENT_SECRET,
        scopes=["https://www.googleapis.com/auth/youtube", "https://www.googleapis.com/auth/youtube.upload"],
    )
    return build("youtube", "v3", credentials=creds)


def get_video_data(video_id: int) -> dict:
    """Get video data from database."""
    sql = f"""
        SELECT id, user_id, storage_path, title, description, tags,
               thumbnail_url, privacy_status, youtube_id, captions,
               youtube_channel_id
        FROM videos WHERE id = {video_id}
    """
    result = run_docker_sql(sql)
    if not result.strip():
        raise ValueError(f"Video {video_id} not found")

    parts = [p.strip() for p in result.split('|')]
    return {
        "id": int(parts[0]),
        "user_id": parts[1],
        "storage_path": parts[2],
        "title": parts[3],
        "description": parts[4],
        "tags": parts[5],
        "thumbnail_url": parts[6],
        "privacy_status": parts[7] or "unlisted",
        "youtube_id": parts[8] if parts[8] else None,
        "captions": json.loads(parts[9]) if parts[9] else None,
        "youtube_channel_id": parts[10] if parts[10] else None
    }


def get_video_captions(video_id: int) -> list[dict]:
    """Get all captions for a video."""
    sql = f"""
        SELECT id, language, language_name, content, format, youtube_caption_id, is_original
        FROM video_captions WHERE video_id = {video_id} ORDER BY is_original DESC, language
    """
    result = run_docker_sql(sql)
    captions = []
    for line in result.split('\n'):
        parts = [p.strip() for p in line.split('|')]
        if len(parts) >= 7 and parts[0]:
            captions.append({
                "id": int(parts[0]),
                "language": parts[1],
                "language_name": parts[2],
                "content": parts[3],
                "format": parts[4],
                "youtube_caption_id": parts[5] if parts[5] else None,
                "is_original": parts[6] == 't'
            })
    return captions


def resumable_upload(request, max_retries: int = 5) -> dict:
    """Execute resumable upload with retry logic."""
    response = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"  Upload progress: {progress}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                if retry < max_retries:
                    retry += 1
                    sleep_time = 2 ** retry
                    print(f"  Server error, retrying in {sleep_time}s...")
                    time.sleep(sleep_time)
                else:
                    raise
            else:
                raise
        except Exception as e:
            if retry < max_retries:
                retry += 1
                sleep_time = 2 ** retry
                print(f"  Error: {e}, retrying in {sleep_time}s...")
                time.sleep(sleep_time)
            else:
                raise

    return response


def upload_video(
    youtube,
    file_path: str,
    title: str,
    description: str,
    tags: list[str],
    privacy_status: str = "unlisted",
    category_id: str = "22"
) -> dict:
    """Upload video to YouTube."""
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")

    file_size = os.path.getsize(file_path)
    print(f"  File: {file_path}")
    print(f"  Size: {file_size / (1024*1024):.1f} MB")

    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": tags[:500],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    media = MediaFileUpload(
        file_path,
        mimetype="video/*",
        chunksize=CHUNK_SIZE,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    response = resumable_upload(request)
    return {
        "youtube_id": response.get("id"),
        "youtube_url": f"https://www.youtube.com/watch?v={response.get('id')}"
    }


def upload_thumbnail(youtube, video_id: str, thumbnail_path: str) -> dict:
    """Upload thumbnail to YouTube video."""
    if not os.path.exists(thumbnail_path):
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")

    ext = os.path.splitext(thumbnail_path)[1].lower()
    mimetype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")

    media = MediaFileUpload(thumbnail_path, mimetype=mimetype)
    response = youtube.thumbnails().set(videoId=video_id, media_body=media).execute()

    return response


def upload_caption(
    youtube,
    video_id: str,
    content: str,
    language: str,
    name: str
) -> dict:
    """Upload caption track to YouTube video."""
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write(content)
        temp_path = f.name

    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
            }
        }

        media = MediaFileUpload(temp_path, mimetype="application/x-subrip")
        response = youtube.captions().insert(
            part="snippet",
            body=body,
            media_body=media
        ).execute()

        return {"caption_id": response.get("id")}
    finally:
        os.unlink(temp_path)


def update_video_metadata(
    youtube,
    video_id: str,
    title: str = None,
    description: str = None,
    tags: list[str] = None,
    category_id: str = None,
    privacy_status: str = None
) -> dict:
    """Update metadata of an existing YouTube video."""
    # First get current video data
    current = youtube.videos().list(part="snippet,status", id=video_id).execute()
    if not current.get("items"):
        raise ValueError(f"Video {video_id} not found on YouTube")

    item = current["items"][0]
    snippet = item["snippet"]
    status = item["status"]

    # Update fields
    if title:
        snippet["title"] = title[:100]
    if description:
        snippet["description"] = description[:5000]
    if tags:
        snippet["tags"] = tags[:500]
    if category_id:
        snippet["categoryId"] = category_id

    body = {"id": video_id, "snippet": snippet}

    if privacy_status:
        body["status"] = {"privacyStatus": privacy_status}

    response = youtube.videos().update(
        part="snippet,status" if privacy_status else "snippet",
        body=body
    ).execute()

    return response


def update_db_video(video_id: int, youtube_id: str, youtube_url: str, channel_id: str, status: str = "published"):
    """Update video record in database."""
    channel_sql = f", youtube_channel_id = '{channel_id}'" if channel_id else ""
    sql = f"""
        UPDATE videos SET
            youtube_id = '{youtube_id}',
            youtube_url = '{youtube_url}',
            status = '{status}'
            {channel_sql}
        WHERE id = {video_id}
    """
    run_docker_sql(sql, fetch=False)


def update_db_caption(video_id: int, language: str, youtube_caption_id: str):
    """Update caption record with YouTube caption ID."""
    sql = f"""
        UPDATE video_captions SET youtube_caption_id = '{youtube_caption_id}'
        WHERE video_id = {video_id} AND language = '{language}'
    """
    run_docker_sql(sql, fetch=False)


def cmd_publish(args):
    """Publish a video to YouTube with all metadata."""
    print(f"\n=== Publishing Video {args.video_id} ===\n")

    # Get video data
    video = get_video_data(args.video_id)
    print(f"Title: {video['title']}")
    print(f"User: {video['user_id']}")

    # Determine channel
    channel_id = args.channel_id or video['youtube_channel_id']
    user_id = args.user_id or video['user_id']

    # Get credentials
    print(f"\nGetting credentials for channel {channel_id or 'default'}...")
    creds = get_channel_credentials(user_id, channel_id)

    # Build YouTube service
    youtube = build_youtube_service(creds)

    # Resolve file path
    storage_path = video['storage_path']
    if storage_path.startswith('uploads/'):
        file_path = os.path.join(VIDEO_UPLOADS_PATH, storage_path.replace('uploads/', ''))
    elif storage_path.startswith('/uploads/'):
        file_path = os.path.join(VIDEO_UPLOADS_PATH, storage_path.replace('/uploads/', ''))
    else:
        file_path = storage_path

    # Upload video
    print(f"\n1. Uploading video...")
    tags = [t.strip() for t in (video['tags'] or '').split(',') if t.strip()]
    result = upload_video(
        youtube,
        file_path,
        video['title'] or 'Untitled',
        video['description'] or '',
        tags,
        video['privacy_status'] or 'unlisted'
    )
    youtube_id = result['youtube_id']
    print(f"   Video uploaded: {result['youtube_url']}")

    # Upload thumbnail
    if video['thumbnail_url']:
        print(f"\n2. Uploading thumbnail...")
        thumb_path = video['thumbnail_url']
        if thumb_path.startswith('/uploads/'):
            thumb_path = os.path.join(VIDEO_UPLOADS_PATH, thumb_path.replace('/uploads/', ''))

        if os.path.exists(thumb_path):
            try:
                upload_thumbnail(youtube, youtube_id, thumb_path)
                print(f"   Thumbnail uploaded!")
            except Exception as e:
                print(f"   Thumbnail upload failed: {e}")
        else:
            print(f"   Thumbnail not found: {thumb_path}")
    else:
        print(f"\n2. No thumbnail to upload")

    # Upload captions
    print(f"\n3. Uploading captions...")
    captions = get_video_captions(args.video_id)

    # If no captions in new table, check old format
    if not captions and video.get('captions'):
        old_captions = video['captions']
        if isinstance(old_captions, dict) and old_captions.get('srt'):
            captions = [{
                "language": "en",
                "language_name": "English",
                "content": old_captions['srt'],
                "is_original": True
            }]

    for cap in captions:
        try:
            result = upload_caption(
                youtube, youtube_id,
                cap['content'],
                cap['language'],
                cap['language_name']
            )
            print(f"   Uploaded {cap['language_name']} captions")
            if cap.get('id'):
                update_db_caption(args.video_id, cap['language'], result['caption_id'])
        except Exception as e:
            print(f"   Failed to upload {cap['language_name']} captions: {e}")

    # Update database
    print(f"\n4. Updating database...")
    update_db_video(args.video_id, youtube_id, f"https://www.youtube.com/watch?v={youtube_id}", channel_id)
    print(f"   Database updated!")

    print(f"\n{'='*50}")
    print(f"PUBLISHED SUCCESSFULLY!")
    print(f"YouTube URL: https://www.youtube.com/watch?v={youtube_id}")
    print(f"{'='*50}\n")


def cmd_captions(args):
    """Upload captions to an existing YouTube video."""
    print(f"\nUploading captions to {args.youtube_id}...")

    creds = get_channel_credentials(args.user_id, args.channel_id)
    youtube = build_youtube_service(creds)

    with open(args.file, 'r', encoding='utf-8') as f:
        content = f.read()

    result = upload_caption(
        youtube, args.youtube_id,
        content, args.language, args.name or f"{args.language} captions"
    )
    print(f"Caption uploaded: {result['caption_id']}")


def cmd_update(args):
    """Update metadata of an existing YouTube video."""
    print(f"\nUpdating video {args.youtube_id}...")

    creds = get_channel_credentials(args.user_id, args.channel_id)
    youtube = build_youtube_service(creds)

    tags = [t.strip() for t in args.tags.split(',')] if args.tags else None

    update_video_metadata(
        youtube, args.youtube_id,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy_status=args.privacy
    )
    print("Video metadata updated!")


def cmd_channels(args):
    """List user's YouTube channels."""
    channels = get_user_channels(args.user_id)
    print(f"\nYouTube channels for {args.user_id}:")
    for ch in channels:
        print(f"  - {ch['account_name']} ({ch['channel_id']})")
        if ch['channel_title']:
            print(f"    Title: {ch['channel_title']}")


def main():
    parser = argparse.ArgumentParser(description="YouTube Publisher")
    subparsers = parser.add_subparsers(dest="command", help="Commands")

    # Publish command
    pub = subparsers.add_parser("publish", help="Publish video to YouTube")
    pub.add_argument("--video-id", "-v", type=int, required=True, help="Video ID from database")
    pub.add_argument("--user-id", "-u", help="User ID (default: from video record)")
    pub.add_argument("--channel-id", "-c", help="YouTube channel ID (default: user's default)")

    # Captions command
    cap = subparsers.add_parser("captions", help="Upload captions to existing video")
    cap.add_argument("--youtube-id", "-y", required=True, help="YouTube video ID")
    cap.add_argument("--file", "-f", required=True, help="Caption file (SRT)")
    cap.add_argument("--language", "-l", default="en", help="Language code")
    cap.add_argument("--name", "-n", help="Caption track name")
    cap.add_argument("--user-id", "-u", required=True, help="User ID")
    cap.add_argument("--channel-id", "-c", help="YouTube channel ID")

    # Update command
    upd = subparsers.add_parser("update", help="Update video metadata")
    upd.add_argument("--youtube-id", "-y", required=True, help="YouTube video ID")
    upd.add_argument("--title", help="New title")
    upd.add_argument("--description", help="New description")
    upd.add_argument("--tags", help="Comma-separated tags")
    upd.add_argument("--privacy", choices=["private", "unlisted", "public"])
    upd.add_argument("--user-id", "-u", required=True, help="User ID")
    upd.add_argument("--channel-id", "-c", help="YouTube channel ID")

    # Channels command
    chn = subparsers.add_parser("channels", help="List user's channels")
    chn.add_argument("--user-id", "-u", required=True, help="User ID")

    args = parser.parse_args()

    if args.command == "publish":
        cmd_publish(args)
    elif args.command == "captions":
        cmd_captions(args)
    elif args.command == "update":
        cmd_update(args)
    elif args.command == "channels":
        cmd_channels(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
