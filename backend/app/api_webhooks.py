"""
n8n Webhook Callbacks
=====================
These endpoints receive async results from n8n workflows.

Since n8n can't always return results directly (due to timeout or async processing),
these webhooks allow n8n to POST results back to update video records.

n8n Workflow Setup:
1. Transcription workflow → calls POST /webhook/caption-result
2. Publish workflow → calls POST /webhook/publish-result
"""
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, HTTPException, BackgroundTasks
from pydantic import BaseModel
from sqlalchemy.orm import Session

from app.db import get_session
from app.models import Video, PublishTransaction

router = APIRouter(prefix="/webhook", tags=["webhooks"])


# ===========================================
# CAPTION RESULT WEBHOOK
# ===========================================

class CaptionResultPayload(BaseModel):
    """Payload sent by n8n after transcription completes."""
    video_id: int
    status: str = "success"  # "success" or "error"
    transcript: Optional[str] = None  # Plain text transcript
    captions_srt: Optional[str] = None  # SRT format captions
    captions_text: Optional[str] = None  # Plain text captions
    language: Optional[str] = "en"
    error_message: Optional[str] = None
    # Optional AI-generated metadata from transcription workflow
    ai_summary: Optional[str] = None
    ai_description: Optional[str] = None
    ai_tags: Optional[str] = None
    # Confidentiality results if checked in same workflow
    confidentiality_status: Optional[str] = None  # pass, warn, fail
    confidentiality_issues: Optional[List[dict]] = None


@router.post("/caption-result")
async def receive_caption_result(payload: CaptionResultPayload):
    """
    Webhook for n8n to POST transcription/caption results.

    n8n workflow should POST to this endpoint after transcription:
    - On success: include transcript, captions_srt or captions_text
    - On error: set status="error" and include error_message

    Example n8n HTTP Request node:
    POST https://video-studio.yourdomain.com/api/webhook/caption-result
    Body (JSON):
    {
      "video_id": {{$node["Get Video"].json.id}},
      "status": "success",
      "transcript": {{$node["Transcribe"].json.text}},
      "captions_srt": {{$node["Transcribe"].json.srt}}
    }
    """
    with get_session() as db:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {payload.video_id} not found")

        if payload.status == "success":
            # Update video with transcription results
            video.transcript = payload.transcript
            video.captions = payload.captions_srt or payload.captions_text or payload.transcript
            video.language = payload.language or video.language
            video.status = "metadata_ready" if video.status == "captioning" else video.status

            # Update AI metadata if provided
            if payload.ai_summary:
                video.ai_summary = payload.ai_summary
                if not video.title:
                    video.title = payload.ai_summary
            if payload.ai_description:
                video.description = payload.ai_description
            if payload.ai_tags:
                video.tags = payload.ai_tags

            # Update confidentiality if provided
            if payload.confidentiality_status:
                video.confidentiality_status = payload.confidentiality_status
            if payload.confidentiality_issues:
                video.confidentiality_issues = payload.confidentiality_issues
        else:
            # Handle error
            video.status = "error"
            video.error_message = payload.error_message or "Transcription failed"

        video.updated_at = datetime.utcnow()
        db.commit()

        return {
            "ok": True,
            "video_id": payload.video_id,
            "status": video.status,
            "message": "Caption result received"
        }


# ===========================================
# PUBLISH RESULT WEBHOOK
# ===========================================

class PublishResultPayload(BaseModel):
    """Payload sent by n8n after YouTube publish completes."""
    video_id: int
    status: str = "success"  # "success" or "error"
    youtube_id: Optional[str] = None  # YouTube video ID
    youtube_url: Optional[str] = None  # Full YouTube URL
    youtube_channel_id: Optional[str] = None
    youtube_response: Optional[dict] = None  # Full API response
    error_message: Optional[str] = None
    # Optional transaction tracking
    transaction_id: Optional[int] = None


@router.post("/publish-result")
async def receive_publish_result(payload: PublishResultPayload):
    """
    Webhook for n8n to POST YouTube publish results.

    n8n workflow should POST to this endpoint after uploading to YouTube:
    - On success: include youtube_id and youtube_url
    - On error: set status="error" and include error_message

    Example n8n HTTP Request node:
    POST https://video-studio.yourdomain.com/api/webhook/publish-result
    Body (JSON):
    {
      "video_id": {{$node["Get Video"].json.id}},
      "status": "success",
      "youtube_id": {{$node["YouTube Upload"].json.id}},
      "youtube_url": "https://youtube.com/watch?v={{$node["YouTube Upload"].json.id}}"
    }
    """
    with get_session() as db:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {payload.video_id} not found")

        if payload.status == "success":
            # Update video with YouTube results
            video.youtube_id = payload.youtube_id
            video.youtube_url = payload.youtube_url or f"https://youtube.com/watch?v={payload.youtube_id}"
            video.youtube_channel_id = payload.youtube_channel_id
            video.youtube_response = payload.youtube_response
            video.status = "published"
            video.published_at = datetime.utcnow()
        else:
            # Handle error
            video.status = "error"
            video.error_message = payload.error_message or "YouTube publish failed"

        video.updated_at = datetime.utcnow()

        # Update transaction if provided
        if payload.transaction_id:
            tx = db.query(PublishTransaction).filter(
                PublishTransaction.id == payload.transaction_id
            ).first()
            if tx:
                tx.status = "success" if payload.status == "success" else "failed"
                tx.response_payload = {
                    "youtube_id": payload.youtube_id,
                    "youtube_url": payload.youtube_url,
                    "error": payload.error_message
                }
                tx.completed_at = datetime.utcnow()
                if payload.error_message:
                    tx.error_message = payload.error_message

        db.commit()

        return {
            "ok": True,
            "video_id": payload.video_id,
            "youtube_id": payload.youtube_id,
            "youtube_url": payload.youtube_url,
            "status": video.status,
            "message": "Publish result received"
        }


# ===========================================
# GENERIC WEBHOOK FOR CUSTOM WORKFLOWS
# ===========================================

class GenericWebhookPayload(BaseModel):
    """Generic payload for custom n8n workflows."""
    video_id: int
    action: str  # e.g., "update_metadata", "update_status"
    data: dict  # Custom data to update


@router.post("/update")
async def generic_update(payload: GenericWebhookPayload):
    """
    Generic webhook for custom n8n workflow updates.

    Allows n8n to update any video fields via a flexible data payload.

    Example:
    POST /api/webhook/update
    {
      "video_id": 123,
      "action": "update_metadata",
      "data": {
        "title": "New Title",
        "description": "New description",
        "tags": "tag1, tag2"
      }
    }
    """
    with get_session() as db:
        video = db.query(Video).filter(Video.id == payload.video_id).first()
        if not video:
            raise HTTPException(status_code=404, detail=f"Video {payload.video_id} not found")

        # Whitelist of allowed fields to update
        allowed_fields = {
            "title", "description", "tags", "hashtags", "status",
            "transcript", "captions", "ai_summary", "thumbnail_url",
            "confidentiality_status", "confidentiality_issues",
            "privacy_status", "category", "language"
        }

        updated_fields = []
        for key, value in payload.data.items():
            if key in allowed_fields and hasattr(video, key):
                setattr(video, key, value)
                updated_fields.append(key)

        video.updated_at = datetime.utcnow()
        db.commit()

        return {
            "ok": True,
            "video_id": payload.video_id,
            "action": payload.action,
            "updated_fields": updated_fields
        }


# ===========================================
# HEALTH CHECK FOR WEBHOOK ENDPOINT
# ===========================================

@router.get("/health")
async def webhook_health():
    """Health check for webhook endpoints."""
    return {
        "status": "healthy",
        "endpoints": [
            "POST /webhook/caption-result",
            "POST /webhook/publish-result",
            "POST /webhook/update"
        ],
        "documentation": "See API docs at /docs for payload schemas"
    }
