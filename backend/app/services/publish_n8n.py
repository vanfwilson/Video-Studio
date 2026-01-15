import httpx
from app.config import settings

async def publish_via_n8n(payload: dict) -> dict:
    """
    Expects your n8n workflow to return JSON like:
      { "youtube_url": "...", "youtube_id": "..." }
    """
    async with httpx.AsyncClient(timeout=300.0) as client:
        r = await client.post(settings.N8N_PUBLISH_URL, json=payload)
        r.raise_for_status()
        return r.json()
