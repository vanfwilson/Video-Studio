import httpx
from app.config import settings

async def transcribe_via_n8n(video_url: str, language_code: str | None = None) -> dict:
    language_code = language_code or settings.DEFAULT_LANGUAGE_CODE

    async with httpx.AsyncClient(timeout=180.0) as client:
        r = await client.post(
            settings.N8N_TRANSCRIBE_URL,
            data={"video_url": video_url, "language_code": language_code},
            headers={"Content-Type": "application/x-www-form-urlencoded"},
        )
        r.raise_for_status()
        return r.json()
