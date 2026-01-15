from datetime import datetime
from fastapi import APIRouter, HTTPException, Depends, Request
from fastapi.responses import RedirectResponse
from sqlalchemy.orm import Session

from app.db import get_db
from app.security import require_user_id
from app.models import Video, PublishTransaction
from app.services.youtube import (
    generate_auth_url,
    exchange_code_for_tokens,
    get_youtube_account
)
from app.services.n8n import publish_via_n8n

router = APIRouter(prefix="/youtube", tags=["youtube"])


@router.get("/status")
def youtube_status(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Check if user has connected YouTube account."""
    account = get_youtube_account(db, user_id)
    
    if not account:
        return {"connected": False}
    
    return {
        "connected": True,
        "account": {
            "platform": "youtube",
            "account_id": account.account_id,
            "account_name": account.account_name,
            "channel_id": account.channel_id,
            "profile_image_url": account.profile_image_url,
            "is_active": account.is_active
        }
    }


@router.post("/auth/start")
def start_youtube_auth(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Start YouTube OAuth flow."""
    try:
        auth_url = generate_auth_url(db, user_id)
        return {"auth_url": auth_url}
    except Exception as e:
        raise HTTPException(500, f"Failed to start OAuth: {str(e)}")


@router.get("/auth/callback")
def youtube_callback(
    code: str,
    state: str,
    request: Request,
    db: Session = Depends(get_db)
):
    """
    Handle YouTube OAuth callback.
    This is called by Google after user authorizes.
    
    Note: We need to get user_id from state since this is a redirect.
    """
    # For OAuth callback, we stored user_id in state lookup
    from app.models import OAuthState
    
    oauth_state = db.query(OAuthState).filter(
        OAuthState.state == state,
        OAuthState.provider == "youtube"
    ).first()
    
    if not oauth_state:
        raise HTTPException(400, "Invalid or expired OAuth state")
    
    user_id = oauth_state.user_id
    
    try:
        result = exchange_code_for_tokens(db, user_id, code, state)
        # Redirect to frontend with success
        return RedirectResponse(url=f"/oauth/youtube/success?channel={result.get('channel_id', '')}")
    except Exception as e:
        # Redirect to frontend with error
        return RedirectResponse(url=f"/oauth/youtube/error?message={str(e)}")


@router.post("/auth/callback")
def youtube_callback_post(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """
    Handle YouTube OAuth callback (POST version for frontend).
    Frontend extracts code/state from URL and posts here.
    """
    code = payload.get("code")
    state = payload.get("state")
    
    if not code or not state:
        raise HTTPException(400, "code and state required")
    
    try:
        result = exchange_code_for_tokens(db, user_id, code, state)
        return {"ok": True, **result}
    except ValueError as e:
        raise HTTPException(400, str(e))
    except Exception as e:
        raise HTTPException(500, f"OAuth exchange failed: {str(e)}")


@router.post("/publish")
async def publish_to_youtube(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Publish video to YouTube via n8n."""
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")
    
    video = db.query(Video).filter(
        Video.id == int(video_id),
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Check YouTube connection
    account = get_youtube_account(db, user_id)
    if not account:
        raise HTTPException(400, "YouTube account not connected. Please connect first.")
    
    # Prepare publish data
    title = payload.get("title") or video.title or video.original_filename
    description = payload.get("description") or video.description or ""
    tags = payload.get("tags") or video.tags or ""
    privacy_status = payload.get("privacy_status") or video.privacy_status or "private"
    category = payload.get("category") or video.category or "22"
    
    # Get captions for closed captions
    captions = ""
    if isinstance(video.captions, dict):
        captions = video.captions.get("srt") or video.captions.get("text") or ""
    
    # Update video status
    video.status = "publishing"
    video.title = title
    video.description = description
    video.tags = tags
    video.privacy_status = privacy_status
    video.category = category
    
    # Create transaction
    publish_payload = {
        "video_url": video.storage_path,
        "title": title,
        "description": description,
        "tags": tags,
        "privacy_status": privacy_status,
        "category": category,
        "captions": captions,
        "channel_id": account.channel_id,
        "user_id": user_id
    }
    
    transaction = PublishTransaction(
        video_id=video.id,
        user_id=user_id,
        action="publish",
        request_payload=publish_payload
    )
    db.add(transaction)
    db.commit()
    
    try:
        result = await publish_via_n8n(publish_payload)
    except Exception as e:
        video.status = "error"
        video.error_message = f"Publish failed: {str(e)}"
        transaction.status = "failed"
        transaction.error_message = str(e)
        transaction.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(502, video.error_message)
    
    # Update video with YouTube info
    video.youtube_id = result.get("youtube_id")
    video.youtube_url = result.get("youtube_url")
    video.youtube_channel_id = result.get("channel_id") or account.channel_id
    video.youtube_response = result
    video.published_at = datetime.utcnow()
    video.status = "published"
    
    transaction.status = "success"
    transaction.response_payload = result
    transaction.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(video)
    
    return {
        "ok": True,
        "youtube_id": video.youtube_id,
        "youtube_url": video.youtube_url,
        "status": video.status
    }


@router.delete("/disconnect")
def disconnect_youtube(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Disconnect YouTube account."""
    account = get_youtube_account(db, user_id)
    if account:
        account.is_active = False
        account.access_token = None
        account.refresh_token = None
        db.commit()
    
    return {"ok": True}
