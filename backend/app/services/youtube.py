import os
import datetime
import secrets
import time
import httpx
from typing import Optional
from sqlalchemy.orm import Session

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload
from googleapiclient.errors import HttpError

from app.config import settings
from app.crypto import encrypt_text, decrypt_text
from app.models import OAuthState, UserSocialAccount

# Chunk size for resumable uploads (50MB - good balance for large files)
CHUNK_SIZE = 50 * 1024 * 1024

def _client_config():
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        raise RuntimeError("Missing YOUTUBE_CLIENT_ID / YOUTUBE_CLIENT_SECRET")
    return {
        "web": {
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "client_secret": settings.YOUTUBE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.YOUTUBE_REDIRECT_URI],
        }
    }

def youtube_flow():
    if not settings.YOUTUBE_REDIRECT_URI:
        raise RuntimeError("Missing YOUTUBE_REDIRECT_URI")
    scopes = settings.YOUTUBE_SCOPES.split()
    flow = Flow.from_client_config(_client_config(), scopes=scopes)
    flow.redirect_uri = settings.YOUTUBE_REDIRECT_URI
    return flow

def create_auth_url(db: Session, user_id: str) -> str:
    flow = youtube_flow()
    state = secrets.token_urlsafe(32)

    db.add(OAuthState(provider="youtube", user_id=user_id, state=state))
    db.commit()

    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        prompt="consent",
        state=state
    )
    return auth_url

def exchange_code(db: Session, user_id: str, code: str, state: str) -> None:
    st = db.query(OAuthState).filter(OAuthState.provider == "youtube", OAuthState.state == state).first()
    if not st or st.user_id != user_id:
        raise ValueError("Invalid OAuth state")
    # consume state
    db.delete(st)
    db.commit()

    flow = youtube_flow()
    flow.fetch_token(code=code)

    creds = flow.credentials
    _store_youtube_credentials(db, user_id=user_id, creds=creds)

def _store_youtube_credentials(db: Session, user_id: str, creds: Credentials) -> None:
    # grab channel info
    yt = build("youtube", "v3", credentials=creds)
    channels = yt.channels().list(part="snippet", mine=True).execute()
    item = (channels.get("items") or [None])[0]
    channel_id = item.get("id") if item else None
    channel_name = item.get("snippet", {}).get("title") if item else None
    thumb = item.get("snippet", {}).get("thumbnails", {}).get("default", {}).get("url") if item else None

    expires_at = None
    if creds.expiry:
        expires_at = creds.expiry.replace(tzinfo=None)

    row = (
        db.query(UserSocialAccount)
        .filter(UserSocialAccount.user_id == user_id, UserSocialAccount.platform == "youtube")
        .first()
    )
    if not row:
        row = UserSocialAccount(user_id=user_id, platform="youtube")

    row.channel_id = channel_id
    row.account_name = channel_name
    row.profile_image_url = thumb

    row.access_token = encrypt_text(creds.token)
    row.refresh_token = encrypt_text(creds.refresh_token)
    row.token_expires_at = expires_at
    row.is_active = True

    db.add(row)
    db.commit()

def _load_creds_from_db(row: UserSocialAccount) -> Credentials:
    scopes = settings.YOUTUBE_SCOPES.split()
    return Credentials(
        token=decrypt_text(row.access_token),
        refresh_token=decrypt_text(row.refresh_token),
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.YOUTUBE_CLIENT_ID,
        client_secret=settings.YOUTUBE_CLIENT_SECRET,
        scopes=scopes,
    )

def youtube_connected(db: Session, user_id: str) -> tuple[bool, Optional[UserSocialAccount]]:
    row = db.query(UserSocialAccount).filter(
        UserSocialAccount.user_id == user_id,
        UserSocialAccount.platform == "youtube",
        UserSocialAccount.is_active == True
    ).first()
    return (row is not None, row)

def list_youtube_channels(db: Session, user_id: str) -> list[dict]:
    """List all YouTube channels connected for this user."""
    rows = db.query(UserSocialAccount).filter(
        UserSocialAccount.user_id == user_id,
        UserSocialAccount.platform == "youtube",
        UserSocialAccount.is_active == True
    ).all()
    return [
        {
            "id": row.id,
            "channel_id": row.channel_id,
            "account_name": row.account_name,
            "profile_image_url": row.profile_image_url,
        }
        for row in rows
    ]

def _resumable_upload(request, max_retries: int = 5) -> dict:
    """
    Execute a resumable upload with retry logic for large files.
    Returns the YouTube API response.
    """
    response = None
    error = None
    retry = 0

    while response is None:
        try:
            status, response = request.next_chunk()
            if status:
                progress = int(status.progress() * 100)
                print(f"Upload progress: {progress}%")
        except HttpError as e:
            if e.resp.status in [500, 502, 503, 504]:
                # Retry on server errors
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
                print(f"Upload error: {e}, retrying in {sleep_time}s (attempt {retry}/{max_retries})")
                time.sleep(sleep_time)
            else:
                raise

    return response

def upload_video_to_youtube(
    db: Session,
    user_id: str,
    file_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy_status: str = "private",
    category_id: str = "22",
    channel_id: str | None = None,
) -> dict:
    """
    Upload a video to YouTube using resumable upload for large files.

    Args:
        db: Database session
        user_id: User ID
        file_path: Path to the video file (local path)
        title: Video title
        description: Video description
        tags: List of tags
        privacy_status: 'private', 'unlisted', or 'public'
        category_id: YouTube category ID (default: 22 = People & Blogs)
        channel_id: Optional specific channel ID if user has multiple channels

    Returns:
        dict with youtube_id and youtube_url
    """
    # Find the right YouTube account
    if channel_id:
        row = db.query(UserSocialAccount).filter(
            UserSocialAccount.user_id == user_id,
            UserSocialAccount.platform == "youtube",
            UserSocialAccount.channel_id == channel_id,
            UserSocialAccount.is_active == True
        ).first()
    else:
        ok, row = youtube_connected(db, user_id)
        if not ok:
            row = None

    if not row:
        raise RuntimeError("YouTube not connected" + (f" for channel {channel_id}" if channel_id else ""))

    creds = _load_creds_from_db(row)
    yt = build("youtube", "v3", credentials=creds)

    # Verify file exists and get size
    if not os.path.exists(file_path):
        raise FileNotFoundError(f"Video file not found: {file_path}")

    file_size = os.path.getsize(file_path)
    print(f"Uploading video: {file_path} ({file_size / (1024*1024):.1f} MB)")

    body = {
        "snippet": {
            "title": title[:100],  # YouTube title limit
            "description": description[:5000],  # YouTube description limit
            "tags": (tags or [])[:500],  # YouTube tags limit
            "categoryId": category_id,
        },
        "status": {
            "privacyStatus": privacy_status,
            "selfDeclaredMadeForKids": False,
        }
    }

    # Use resumable upload with chunking for large files
    media = MediaFileUpload(
        file_path,
        mimetype="video/*",
        chunksize=CHUNK_SIZE,
        resumable=True
    )

    request = yt.videos().insert(
        part="snippet,status",
        body=body,
        media_body=media
    )

    # Execute with retry logic
    response = _resumable_upload(request)

    video_id = response.get("id")
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None

    print(f"Upload complete! Video ID: {video_id}")

    return {"youtube_id": video_id, "youtube_url": url}

def upload_thumbnail(
    db: Session,
    user_id: str,
    video_id: str,
    thumbnail_path: str,
    channel_id: str | None = None,
) -> dict:
    """Upload a custom thumbnail for a YouTube video."""
    if channel_id:
        row = db.query(UserSocialAccount).filter(
            UserSocialAccount.user_id == user_id,
            UserSocialAccount.platform == "youtube",
            UserSocialAccount.channel_id == channel_id,
            UserSocialAccount.is_active == True
        ).first()
    else:
        ok, row = youtube_connected(db, user_id)
        if not ok:
            row = None

    if not row:
        raise RuntimeError("YouTube not connected")

    creds = _load_creds_from_db(row)
    yt = build("youtube", "v3", credentials=creds)

    media = MediaFileUpload(thumbnail_path, mimetype="image/*")
    response = yt.thumbnails().set(videoId=video_id, media_body=media).execute()

    return {"thumbnail_url": response.get("items", [{}])[0].get("default", {}).get("url")}

def upload_captions(
    db: Session,
    user_id: str,
    video_id: str,
    captions_content: str,
    language: str = "en",
    name: str = "English",
    channel_id: str | None = None,
) -> dict:
    """Upload captions/subtitles for a YouTube video."""
    if channel_id:
        row = db.query(UserSocialAccount).filter(
            UserSocialAccount.user_id == user_id,
            UserSocialAccount.platform == "youtube",
            UserSocialAccount.channel_id == channel_id,
            UserSocialAccount.is_active == True
        ).first()
    else:
        ok, row = youtube_connected(db, user_id)
        if not ok:
            row = None

    if not row:
        raise RuntimeError("YouTube not connected")

    creds = _load_creds_from_db(row)
    yt = build("youtube", "v3", credentials=creds)

    # Write captions to temp file
    import tempfile
    with tempfile.NamedTemporaryFile(mode='w', suffix='.srt', delete=False) as f:
        f.write(captions_content)
        temp_path = f.name

    try:
        body = {
            "snippet": {
                "videoId": video_id,
                "language": language,
                "name": name,
            }
        }

        media = MediaFileUpload(temp_path, mimetype="text/plain")
        response = yt.captions().insert(
            part="snippet",
            body=body,
            media_body=media
        ).execute()

        return {"caption_id": response.get("id")}
    finally:
        os.unlink(temp_path)

async def download_file_to_temp(url: str, suffix: str = ".mp4") -> str:
    """Download a file from URL to a temporary location."""
    import tempfile

    temp_file = tempfile.NamedTemporaryFile(delete=False, suffix=suffix)
    temp_path = temp_file.name
    temp_file.close()

    async with httpx.AsyncClient(timeout=600.0) as client:
        async with client.stream("GET", url) as response:
            response.raise_for_status()
            with open(temp_path, "wb") as f:
                async for chunk in response.aiter_bytes(chunk_size=8192):
                    f.write(chunk)

    return temp_path
