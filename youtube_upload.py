#!/usr/bin/env python3
"""
Standalone YouTube uploader that uses n8n credentials.
Usage: python youtube_upload.py <video_path> <title> [--channel <channel_name>]
"""

import os
import sys
import json
import base64
import argparse
import time
from typing import Optional
from cryptography.hazmat.primitives.ciphers import Cipher, algorithms, modes
from cryptography.hazmat.backends import default_backend
import psycopg2

from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

# n8n encryption key (from environment)
N8N_ENCRYPTION_KEY = os.environ.get("N8N_ENCRYPTION_KEY", "gcCUrehj1pvVeFr+DZ6JEIOU9632wN2n")

# Database connection
N8N_DB_HOST = os.environ.get("N8N_DB_HOST", "localhost")
N8N_DB_PORT = os.environ.get("N8N_DB_PORT", "5433")  # n8n-3a-postgres exposed port
N8N_DB_NAME = os.environ.get("N8N_DB_NAME", "n8n")
N8N_DB_USER = os.environ.get("N8N_DB_USER", "n8n")
N8N_DB_PASSWORD = os.environ.get("N8N_DB_PASSWORD", "Masaya9989")

# YouTube OAuth client (same as n8n uses)
YOUTUBE_CLIENT_ID = os.environ.get("YOUTUBE_CLIENT_ID", "10404446139-9tlvhjoicaf8ejsts4jaa1te761tsdvm.apps.googleusercontent.com")
YOUTUBE_CLIENT_SECRET = os.environ.get("YOUTUBE_CLIENT_SECRET", "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")

# Chunk size for resumable uploads (50MB)
CHUNK_SIZE = 50 * 1024 * 1024


def decrypt_n8n_credential(encrypted_data: str, encryption_key: str) -> dict:
    """
    Decrypt n8n encrypted credential data.
    n8n uses AES-256-CBC with the format: Salted__<8-byte-salt><ciphertext>
    """
    import hashlib

    # Decode base64
    data = base64.b64decode(encrypted_data)

    # Check for "Salted__" prefix
    if data[:8] != b"Salted__":
        raise ValueError("Invalid encrypted data format")

    salt = data[8:16]
    ciphertext = data[16:]

    # Derive key and IV using OpenSSL's EVP_BytesToKey (MD5-based)
    key_iv = b""
    prev = b""
    while len(key_iv) < 48:  # 32 bytes key + 16 bytes IV
        prev = hashlib.md5(prev + encryption_key.encode() + salt).digest()
        key_iv += prev

    key = key_iv[:32]
    iv = key_iv[32:48]

    # Decrypt
    cipher = Cipher(algorithms.AES(key), modes.CBC(iv), backend=default_backend())
    decryptor = cipher.decryptor()
    decrypted = decryptor.update(ciphertext) + decryptor.finalize()

    # Remove PKCS7 padding
    padding_len = decrypted[-1]
    decrypted = decrypted[:-padding_len]

    return json.loads(decrypted.decode('utf-8'))


def get_youtube_credentials_from_n8n(channel_name: str = "YouTube Askstephen") -> dict:
    """Get YouTube OAuth credentials from n8n database."""
    conn = psycopg2.connect(
        host=N8N_DB_HOST,
        port=N8N_DB_PORT,
        database=N8N_DB_NAME,
        user=N8N_DB_USER,
        password=N8N_DB_PASSWORD
    )

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT data FROM credentials_entity WHERE name = %s AND type = 'youTubeOAuth2Api'",
            (channel_name,)
        )
        row = cur.fetchone()
        if not row:
            raise ValueError(f"YouTube credential '{channel_name}' not found in n8n")

        encrypted_data = row[0]
        creds_data = decrypt_n8n_credential(encrypted_data, N8N_ENCRYPTION_KEY)
        return creds_data
    finally:
        conn.close()


def list_available_channels() -> list[str]:
    """List all YouTube channels available in n8n."""
    conn = psycopg2.connect(
        host=N8N_DB_HOST,
        port=N8N_DB_PORT,
        database=N8N_DB_NAME,
        user=N8N_DB_USER,
        password=N8N_DB_PASSWORD
    )

    try:
        cur = conn.cursor()
        cur.execute(
            "SELECT name FROM credentials_entity WHERE type = 'youTubeOAuth2Api' ORDER BY name"
        )
        return [row[0] for row in cur.fetchall()]
    finally:
        conn.close()


def build_youtube_service(creds_data: dict):
    """Build YouTube API service from credential data."""
    # n8n stores tokens inside oauthTokenData
    token_data = creds_data.get("oauthTokenData", {})
    if isinstance(token_data, str):
        token_data = json.loads(token_data)

    # Get client credentials from the main object or use defaults
    client_id = creds_data.get("clientId") or YOUTUBE_CLIENT_ID
    client_secret = creds_data.get("clientSecret") or YOUTUBE_CLIENT_SECRET

    creds = Credentials(
        token=token_data.get("access_token"),
        refresh_token=token_data.get("refresh_token"),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=client_id,
        client_secret=client_secret,
        scopes=["https://www.googleapis.com/auth/youtube.upload", "https://www.googleapis.com/auth/youtube"],
    )
    return build("youtube", "v3", credentials=creds)


def resumable_upload(request, max_retries: int = 5) -> dict:
    """Execute resumable upload with retry logic."""
    response = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"Upload progress: {progress}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                if retry < max_retries:
                    retry += 1
                    sleep_time = 2 ** retry
                    print(f"Server error, retrying in {sleep_time}s (attempt {retry}/{max_retries})")
                    time.sleep(sleep_time)
                else:
                    raise
            else:
                raise
        except Exception as e:
            if retry < max_retries:
                retry += 1
                sleep_time = 2 ** retry
                print(f"Upload error: {e}, retrying in {sleep_time}s")
                time.sleep(sleep_time)
            else:
                raise

    return response


def upload_video(
    video_path: str,
    title: str,
    description: str = "",
    tags: list[str] = None,
    privacy_status: str = "unlisted",
    category_id: str = "22",
    channel_name: str = "YouTube Askstephen",
) -> dict:
    """Upload a video to YouTube."""

    if not os.path.exists(video_path):
        raise FileNotFoundError(f"Video file not found: {video_path}")

    file_size = os.path.getsize(video_path)
    print(f"Video file: {video_path}")
    print(f"File size: {file_size / (1024*1024):.1f} MB")
    print(f"Channel: {channel_name}")
    print(f"Title: {title}")
    print(f"Privacy: {privacy_status}")
    print()

    # Get credentials from n8n
    print("Getting YouTube credentials from n8n...")
    creds_data = get_youtube_credentials_from_n8n(channel_name)

    # Build YouTube service
    print("Building YouTube API service...")
    youtube = build_youtube_service(creds_data)

    # Prepare video metadata
    body = {
        "snippet": {
            "title": title[:100],
            "description": description[:5000],
            "tags": (tags or [])[:500],
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    # Create media upload
    print("Starting upload...")
    media = MediaFileUpload(
        video_path,
        mimetype="video/*",
        chunksize=CHUNK_SIZE,
        resumable=True
    )

    request = youtube.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Execute upload
    response = resumable_upload(request)

    video_id = response.get("id")
    url = f"https://www.youtube.com/watch?v={video_id}"

    print()
    print("=" * 50)
    print(f"Upload complete!")
    print(f"Video ID: {video_id}")
    print(f"URL: {url}")
    print("=" * 50)

    return {"youtube_id": video_id, "youtube_url": url}


def upload_thumbnail(
    youtube_video_id: str,
    thumbnail_path: str,
    channel_name: str = "YouTube Askstephen",
) -> dict:
    """Upload a thumbnail for a YouTube video."""

    if not os.path.exists(thumbnail_path):
        raise FileNotFoundError(f"Thumbnail not found: {thumbnail_path}")

    creds_data = get_youtube_credentials_from_n8n(channel_name)
    youtube = build_youtube_service(creds_data)

    # Determine mimetype from file extension
    ext = os.path.splitext(thumbnail_path)[1].lower()
    mimetype = {"png": "image/png", "jpg": "image/jpeg", "jpeg": "image/jpeg"}.get(ext.lstrip("."), "image/png")
    media = MediaFileUpload(thumbnail_path, mimetype=mimetype)
    response = youtube.thumbnails().set(
        videoId=youtube_video_id,
        media_body=media
    ).execute()

    return response


def main():
    parser = argparse.ArgumentParser(description="Upload video to YouTube using n8n credentials")
    parser.add_argument("video_path", nargs="?", help="Path to video file")
    parser.add_argument("title", nargs="?", help="Video title")
    parser.add_argument("--description", "-d", default="", help="Video description")
    parser.add_argument("--tags", "-t", default="", help="Comma-separated tags")
    parser.add_argument("--privacy", "-p", default="unlisted", choices=["private", "unlisted", "public"])
    parser.add_argument("--channel", "-c", default="YouTube Askstephen", help="n8n credential name")
    parser.add_argument("--list-channels", action="store_true", help="List available YouTube channels")
    parser.add_argument("--thumbnail", help="Path to thumbnail image")
    parser.add_argument("--video-id", help="YouTube video ID (for thumbnail upload)")

    args = parser.parse_args()

    if args.list_channels:
        print("Available YouTube channels in n8n:")
        for name in list_available_channels():
            print(f"  - {name}")
        return

    if args.video_id and args.thumbnail:
        # Upload thumbnail only
        result = upload_thumbnail(args.video_id, args.thumbnail, args.channel)
        print(f"Thumbnail uploaded: {result}")
        return

    if not args.video_path or not args.title:
        parser.print_help()
        sys.exit(1)

    tags = [t.strip() for t in args.tags.split(",") if t.strip()] if args.tags else []

    result = upload_video(
        video_path=args.video_path,
        title=args.title,
        description=args.description,
        tags=tags,
        privacy_status=args.privacy,
        channel_name=args.channel,
    )

    # Upload thumbnail if provided
    if args.thumbnail and result.get("youtube_id"):
        print("\nUploading thumbnail...")
        upload_thumbnail(result["youtube_id"], args.thumbnail, args.channel)
        print("Thumbnail uploaded!")


if __name__ == "__main__":
    main()
