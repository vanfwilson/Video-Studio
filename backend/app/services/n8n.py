"""
n8n Webhook Integration
=======================
Calls your existing n8n webhooks for transcription and publishing.

Supports two modes:
1. Synchronous: n8n returns results immediately (if workflow is fast)
2. Async/Callback: n8n processes async and calls back to our webhook endpoints

Your n8n webhooks:
- N8N_TRANSCRIBE_URL: Your existing transcription workflow
- N8N_PUBLISH_URL: Your existing YouTube publish workflow

Callback URLs (for n8n to send results back):
- /api/webhook/caption-result: Receives transcription results
- /api/webhook/publish-result: Receives publish results
"""
import httpx
from typing import Optional
from app.config import settings


async def transcribe_via_n8n(
    video_url: str,
    video_id: int,
    language_code: str | None = None,
    callback_url: str | None = None
) -> dict:
    """
    Call n8n webhook to transcribe a video.

    Sends to your existing n8n transcription workflow:
    - video_url: Public URL where n8n can download the video
    - video_id: Video ID for callback identification
    - language_code: Language for transcription (default: en)
    - callback_url: URL for n8n to POST results back (async mode)

    If n8n returns results immediately (sync mode), returns them.
    If n8n processes async, it should POST results to callback_url.

    Expected n8n response (sync mode):
    {
        "text": "Full transcript text...",
        "srt": "1\n00:00:00,000 --> 00:00:05,000\nSubtitle text..."
    }

    For async mode, n8n should POST to callback_url:
    {
        "video_id": 123,
        "status": "success",
        "transcript": "...",
        "captions_srt": "..."
    }
    """
    language_code = language_code or settings.DEFAULT_LANGUAGE_CODE

    # Build callback URL if not provided
    if not callback_url:
        callback_url = f"{settings.PUBLIC_BASE_URL}/api/webhook/caption-result"

    payload = {
        "video_url": video_url,
        "video_id": video_id,
        "language_code": language_code,
        "callback_url": callback_url,
        "action": "transcribe"
    }

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            settings.N8N_TRANSCRIBE_URL,
            data=payload,  # form-encoded as your existing workflow expects
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()

        # Try to parse response - may be empty if async
        try:
            result = response.json()
            if result:
                return result
        except Exception:
            pass

        # Return empty dict if async (results will come via callback)
        return {"async": True, "message": "Processing started, results via callback"}


async def publish_via_n8n(
    video_id: int,
    video_url: str,
    title: str,
    description: str,
    tags: str = "",
    privacy_status: str = "private",
    category: str = "22",
    captions: str = "",
    thumbnail_url: Optional[str] = None,
    callback_url: str | None = None
) -> dict:
    """
    Call n8n webhook to publish a video to YouTube.

    Sends to your existing n8n YouTube publish workflow:
    - video_id: Video ID for callback identification
    - video_url: Public URL where n8n can download the video
    - title, description, tags: YouTube metadata
    - privacy_status: private, unlisted, or public
    - category: YouTube category ID (22 = People & Blogs)
    - captions: SRT content for closed captions
    - callback_url: URL for n8n to POST results back (async mode)

    If n8n returns results immediately (sync mode), returns them.
    If n8n processes async, it should POST results to callback_url.

    Expected n8n response (sync mode):
    {
        "youtube_id": "abc123",
        "youtube_url": "https://youtube.com/watch?v=abc123"
    }

    For async mode, n8n should POST to callback_url:
    {
        "video_id": 123,
        "status": "success",
        "youtube_id": "abc123",
        "youtube_url": "https://youtube.com/watch?v=abc123"
    }
    """
    # Build callback URL if not provided
    if not callback_url:
        callback_url = f"{settings.PUBLIC_BASE_URL}/api/webhook/publish-result"

    payload = {
        "video_id": video_id,
        "video_url": video_url,
        "title": title,
        "description": description,
        "tags": tags,
        "privacy_status": privacy_status,
        "category": category,
        "captions": captions,
        "callback_url": callback_url,
        "action": "publish"
    }

    if thumbnail_url:
        payload["thumbnail_url"] = thumbnail_url

    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            settings.N8N_PUBLISH_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()

        # Try to parse response - may be empty if async
        try:
            result = response.json()
            if result:
                return result
        except Exception:
            pass

        # Return empty dict if async (results will come via callback)
        return {"async": True, "message": "Publishing started, results via callback"}
