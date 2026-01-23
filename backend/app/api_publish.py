"""
Publish API - Handles publishing videos to YouTube via n8n.

n8n has the actual YouTube API credentials. This API:
1. Gets the video details from our database
2. Gets the user's selected YouTube channel from cloud_connections
3. Calls n8n webhook to do the actual upload
4. Stores the resulting YouTube URL back in our database

Supports:
- Custom thumbnail upload
- Multi-language captions (1-30 languages)
- Privacy status (defaults to unlisted)
"""
import os
import tempfile
import httpx
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from typing import Optional

from app.db import SessionLocal
from app.security import require_user_id
from app.models import Video, CloudConnection
from app.config import settings

router = APIRouter(prefix="/publish", tags=["publish"])

def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def extract_captions(video: Video) -> list[dict]:
    """
    Extract captions from video.captions JSONB field.

    Expected formats:
    1. Single language (legacy): {"format": "srt", "srt": "content..."}
    2. Multi-language: {
         "en": {"format": "srt", "content": "...", "url": "..."},
         "es": {"format": "srt", "content": "...", "url": "..."},
         ...
       }

    Returns list of caption objects for n8n:
    [
        {"language": "en", "format": "srt", "content": "...", "url": "..."},
        {"language": "es", "format": "srt", "content": "...", "url": "..."},
    ]
    """
    if not video.captions:
        return []

    captions = video.captions
    result = []

    # Check if it's the legacy single-language format
    if "srt" in captions or "text" in captions or "format" in captions:
        # Legacy format - use video.language as the language code
        lang = video.language or "en"
        content = captions.get("srt") or captions.get("text") or captions.get("content")
        url = captions.get("url")
        fmt = captions.get("format", "srt")
        if content or url:
            result.append({
                "language": lang,
                "format": fmt,
                "content": content,
                "url": url
            })
    else:
        # Multi-language format - keys are language codes
        for lang_code, caption_data in captions.items():
            if isinstance(caption_data, dict):
                result.append({
                    "language": lang_code,
                    "format": caption_data.get("format", "srt"),
                    "content": caption_data.get("content") or caption_data.get("srt") or caption_data.get("text"),
                    "url": caption_data.get("url")
                })
            elif isinstance(caption_data, str):
                # Simple format: {"en": "caption content..."}
                result.append({
                    "language": lang_code,
                    "format": "srt",
                    "content": caption_data,
                    "url": None
                })

    return result

@router.post("/youtube")
async def publish_to_youtube(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """
    Publish a video to YouTube via n8n.

    Payload:
    {
        "video_id": 123,
        "title": "optional override",
        "description": "optional override",
        "tags": "comma,separated,tags",
        "privacy_status": "unlisted" (default) | "private" | "public",
        "channel_id": "optional - uses default if not specified",
        "thumbnail_url": "optional - override video's thumbnail_url",
        "captions": [  // optional - override video's captions
            {"language": "en", "format": "srt", "content": "..."},
            {"language": "es", "format": "srt", "url": "https://..."}
        ]
    }

    n8n webhook receives:
    {
        "video_url": "https://...",
        "title": "...",
        "description": "...",
        "tags": ["tag1", "tag2"],
        "privacy_status": "unlisted",
        "channel_id": "UCxxxxxx",
        "thumbnail_url": "https://... or null",
        "captions": [
            {"language": "en", "format": "srt", "content": "...", "url": "..."},
            ...
        ],
        "user_id": "...",
        "video_id": 123
    }

    n8n returns:
    {
        "youtube_id": "abc123",
        "youtube_url": "https://youtube.com/watch?v=abc123"
    }
    """
    if not settings.N8N_PUBLISH_URL:
        raise HTTPException(500, "N8N_PUBLISH_URL not configured. Set it in .env")

    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")

    # Get video
    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    # Get YouTube channel connection
    channel_id = payload.get("channel_id")
    if not channel_id:
        # Look for user's YouTube connection
        yt_conn = db.query(CloudConnection).filter(
            CloudConnection.user_id == user_id,
            CloudConnection.provider == "youtube",
            CloudConnection.is_active == "true"
        ).first()
        if yt_conn:
            channel_id = yt_conn.account_id

    if not channel_id:
        raise HTTPException(400, "No YouTube channel connected. Please connect a YouTube channel first.")

    # Prepare publish data
    title = payload.get("title") or v.title or v.original_filename
    description = payload.get("description") or v.description or ""
    tags_str = payload.get("tags") or v.tags or ""
    # Default to unlisted
    privacy_status = payload.get("privacy_status") or v.privacy_status or "unlisted"

    # Thumbnail - use override or video's thumbnail
    thumbnail_url = payload.get("thumbnail_url") or v.thumbnail_url

    # Captions - use override or extract from video
    captions = payload.get("captions")
    if captions is None:
        captions = extract_captions(v)

    tags = [t.strip() for t in tags_str.split(",") if t.strip()] if isinstance(tags_str, str) else tags_str

    # Get video URL
    video_url = v.storage_path
    if not video_url:
        raise HTTPException(400, "Video has no storage_path")

    # Update status
    v.status = "publishing"
    v.error_message = None
    db.add(v)
    db.commit()

    try:
        # Call n8n webhook
        n8n_payload = {
            "video_url": video_url,
            "title": title,
            "description": description,
            "tags": tags,
            "privacy_status": privacy_status,
            "channel_id": channel_id,
            "thumbnail_url": thumbnail_url,
            "captions": captions,
            "user_id": user_id,
            "video_id": v.id,
        }

        async with httpx.AsyncClient(timeout=600.0) as client:
            r = await client.post(settings.N8N_PUBLISH_URL, json=n8n_payload)
            r.raise_for_status()
            result = r.json()

        # Update video with YouTube info
        v.youtube_id = result.get("youtube_id")
        v.youtube_url = result.get("youtube_url")
        v.status = "published"
        v.privacy_status = privacy_status  # Store what was actually published
        db.add(v)
        db.commit()
        db.refresh(v)

        return {
            "ok": True,
            "youtube_id": v.youtube_id,
            "youtube_url": v.youtube_url,
            "status": v.status,
            "captions_uploaded": len(captions) if captions else 0
        }

    except httpx.HTTPStatusError as e:
        v.status = "failed"
        v.error_message = f"n8n publish failed: HTTP {e.response.status_code}"
        db.add(v)
        db.commit()
        raise HTTPException(502, v.error_message)
    except Exception as e:
        v.status = "failed"
        v.error_message = f"Publish failed: {str(e)}"
        db.add(v)
        db.commit()
        raise HTTPException(500, v.error_message)

@router.get("/youtube/channels")
def list_youtube_channels(
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """List available YouTube channels for the user."""
    channels = db.query(CloudConnection).filter(
        CloudConnection.user_id == user_id,
        CloudConnection.provider == "youtube"
    ).all()

    return [
        {
            "id": c.id,
            "channel_id": c.account_id,
            "channel_name": c.account_name,
            "profile_photo_url": c.profile_photo_url,
            "is_active": c.is_active == "true"
        }
        for c in channels
    ]

@router.post("/youtube/captions")
async def add_captions_to_video(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """
    Add captions to an existing video's database record.

    Payload:
    {
        "video_id": 123,
        "language": "en",
        "format": "srt",
        "content": "1\n00:00:00,000 --> 00:00:05,000\nHello world\n\n..."
    }

    Or to add multiple at once:
    {
        "video_id": 123,
        "captions": [
            {"language": "en", "format": "srt", "content": "..."},
            {"language": "es", "format": "srt", "content": "..."}
        ]
    }
    """
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")

    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    # Get existing captions or initialize
    existing_captions = v.captions or {}

    # Handle legacy format - convert to multi-language
    if "srt" in existing_captions or "text" in existing_captions or "format" in existing_captions:
        lang = v.language or "en"
        legacy_content = existing_captions.get("srt") or existing_captions.get("text") or existing_captions.get("content")
        existing_captions = {
            lang: {
                "format": existing_captions.get("format", "srt"),
                "content": legacy_content
            }
        }

    # Add new captions
    captions_list = payload.get("captions")
    if captions_list:
        for cap in captions_list:
            lang = cap.get("language")
            if lang:
                existing_captions[lang] = {
                    "format": cap.get("format", "srt"),
                    "content": cap.get("content"),
                    "url": cap.get("url")
                }
    else:
        # Single caption
        lang = payload.get("language")
        if lang:
            existing_captions[lang] = {
                "format": payload.get("format", "srt"),
                "content": payload.get("content"),
                "url": payload.get("url")
            }

    v.captions = existing_captions
    db.add(v)
    db.commit()
    db.refresh(v)

    return {
        "ok": True,
        "video_id": v.id,
        "languages": list(existing_captions.keys()),
        "caption_count": len(existing_captions)
    }
