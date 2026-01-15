import secrets
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from google.oauth2.credentials import Credentials
from google_auth_oauthlib.flow import Flow
from googleapiclient.discovery import build

from app.config import settings
from app.models import UserSocialAccount, OAuthState

# YouTube OAuth scopes
SCOPES = settings.YOUTUBE_SCOPES.split()


def create_oauth_flow() -> Flow:
    """Create Google OAuth flow for YouTube."""
    if not settings.YOUTUBE_CLIENT_ID or not settings.YOUTUBE_CLIENT_SECRET:
        raise RuntimeError("YouTube OAuth credentials not configured")
    
    client_config = {
        "web": {
            "client_id": settings.YOUTUBE_CLIENT_ID,
            "client_secret": settings.YOUTUBE_CLIENT_SECRET,
            "auth_uri": "https://accounts.google.com/o/oauth2/auth",
            "token_uri": "https://oauth2.googleapis.com/token",
            "redirect_uris": [settings.YOUTUBE_REDIRECT_URI]
        }
    }
    
    flow = Flow.from_client_config(
        client_config,
        scopes=SCOPES,
        redirect_uri=settings.YOUTUBE_REDIRECT_URI
    )
    return flow


def generate_auth_url(db: Session, user_id: str) -> str:
    """
    Generate YouTube OAuth authorization URL.
    Stores state for CSRF protection.
    """
    flow = create_oauth_flow()
    state = secrets.token_urlsafe(32)
    
    # Store state for verification
    db.query(OAuthState).filter(
        OAuthState.user_id == user_id,
        OAuthState.provider == "youtube"
    ).delete()
    
    db.add(OAuthState(
        provider="youtube",
        user_id=user_id,
        state=state
    ))
    db.commit()
    
    auth_url, _ = flow.authorization_url(
        access_type="offline",
        include_granted_scopes="true",
        state=state,
        prompt="consent"
    )
    return auth_url


def exchange_code_for_tokens(db: Session, user_id: str, code: str, state: str) -> dict:
    """
    Exchange authorization code for tokens and store them.
    """
    # Verify state
    stored_state = db.query(OAuthState).filter(
        OAuthState.user_id == user_id,
        OAuthState.provider == "youtube",
        OAuthState.state == state
    ).first()
    
    if not stored_state:
        raise ValueError("Invalid or expired OAuth state")
    
    # Clean up state
    db.delete(stored_state)
    db.commit()
    
    # Exchange code for tokens
    flow = create_oauth_flow()
    flow.fetch_token(code=code)
    credentials = flow.credentials
    
    # Get YouTube channel info
    youtube = build("youtube", "v3", credentials=credentials)
    channels = youtube.channels().list(part="snippet", mine=True).execute()
    
    channel_info = {}
    if channels.get("items"):
        ch = channels["items"][0]
        channel_info = {
            "channel_id": ch["id"],
            "account_name": ch["snippet"]["title"],
            "profile_image_url": ch["snippet"]["thumbnails"]["default"]["url"]
        }
    
    # Store or update social account
    existing = db.query(UserSocialAccount).filter(
        UserSocialAccount.user_id == user_id,
        UserSocialAccount.platform == "youtube"
    ).first()
    
    if existing:
        existing.access_token = credentials.token
        existing.refresh_token = credentials.refresh_token
        existing.token_expires_at = credentials.expiry
        existing.channel_id = channel_info.get("channel_id")
        existing.account_name = channel_info.get("account_name")
        existing.profile_image_url = channel_info.get("profile_image_url")
        existing.is_active = True
    else:
        existing = UserSocialAccount(
            user_id=user_id,
            platform="youtube",
            access_token=credentials.token,
            refresh_token=credentials.refresh_token,
            token_expires_at=credentials.expiry,
            channel_id=channel_info.get("channel_id"),
            account_name=channel_info.get("account_name"),
            profile_image_url=channel_info.get("profile_image_url"),
            is_active=True
        )
        db.add(existing)
    
    db.commit()
    
    return {
        "ok": True,
        "channel_id": channel_info.get("channel_id"),
        "account_name": channel_info.get("account_name")
    }


def get_youtube_account(db: Session, user_id: str) -> Optional[UserSocialAccount]:
    """Get the user's YouTube social account."""
    return db.query(UserSocialAccount).filter(
        UserSocialAccount.user_id == user_id,
        UserSocialAccount.platform == "youtube",
        UserSocialAccount.is_active == True
    ).first()


def get_credentials(account: UserSocialAccount) -> Optional[Credentials]:
    """Get Google credentials from stored social account."""
    if not account or not account.access_token:
        return None
    
    credentials = Credentials(
        token=account.access_token,
        refresh_token=account.refresh_token,
        token_uri="https://oauth2.googleapis.com/token",
        client_id=settings.YOUTUBE_CLIENT_ID,
        client_secret=settings.YOUTUBE_CLIENT_SECRET,
        expiry=account.token_expires_at
    )
    return credentials


def is_token_valid(account: UserSocialAccount) -> bool:
    """Check if the stored token is still valid."""
    if not account or not account.token_expires_at:
        return False
    return account.token_expires_at > datetime.utcnow() + timedelta(minutes=5)
