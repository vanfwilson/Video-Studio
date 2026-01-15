import httpx
from app.config import settings

async def transcribe_via_n8n(video_url: str, language_code: str | None = None) -> dict:
    """
    Call n8n webhook to transcribe a video.
    
    Expected n8n response:
    {
        "text": "Full transcript text...",
        "srt": "1\n00:00:00,000 --> 00:00:05,000\nSubtitle text..."
    }
    """
    language_code = language_code or settings.DEFAULT_LANGUAGE_CODE

    async with httpx.AsyncClient(timeout=300.0) as client:
        response = await client.post(
            settings.N8N_TRANSCRIBE_URL,
            data={
                "video_url": video_url,
                "language_code": language_code
            },
            headers={"Content-Type": "application/x-www-form-urlencoded"}
        )
        response.raise_for_status()
        return response.json()


async def publish_via_n8n(payload: dict) -> dict:
    """
    Call n8n webhook to publish a video to YouTube.
    
    Expected payload:
    {
        "video_url": "https://...",
        "title": "...",
        "description": "...",
        "tags": "tag1,tag2",
        "privacy_status": "private|unlisted|public",
        "category": "22",
        "captions": "SRT content or empty"
    }
    
    Expected n8n response:
    {
        "youtube_id": "abc123",
        "youtube_url": "https://youtube.com/watch?v=abc123"
    }
    """
    async with httpx.AsyncClient(timeout=600.0) as client:
        response = await client.post(
            settings.N8N_PUBLISH_URL,
            json=payload,
            headers={"Content-Type": "application/json"}
        )
        response.raise_for_status()
        return response.json()
