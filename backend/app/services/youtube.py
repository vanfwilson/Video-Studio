import datetime
import secrets
from typing import Optional
from sqlalchemy.orm import Session

from google_auth_oauthlib.flow import Flow
from google.oauth2.credentials import Credentials
from googleapiclient.discovery import build
from googleapiclient.http import MediaFileUpload

from app.config import settings
from app.crypto import encrypt_text, decrypt_text
from app.models import OAuthState, UserSocialAccount

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

def upload_video_to_youtube(
    db: Session,
    user_id: str,
    file_path: str,
    title: str,
    description: str,
    tags: list[str] | None = None,
    privacy_status: str = "private",
) -> dict:
    ok, row = youtube_connected(db, user_id)
    if not ok or not row:
        raise RuntimeError("YouTube not connected")

    creds = _load_creds_from_db(row)
    yt = build("youtube", "v3", credentials=creds)

    body = {
        "snippet": {
            "title": title,
            "description": description,
            "tags": tags or [],
            "categoryId": "22",  # People & Blogs (safe default)
        },
        "status": {
            "privacyStatus": privacy_status
        }
    }

    media = MediaFileUpload(file_path, chunksize=-1, resumable=True)

    req = yt.videos().insert(part="snippet,status", body=body, media_body=media)
    resp = req.execute()
    video_id = resp.get("id")
    url = f"https://www.youtube.com/watch?v={video_id}" if video_id else None
    return {"youtube_id": video_id, "youtube_url": url}
