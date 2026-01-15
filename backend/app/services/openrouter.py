import httpx
from app.config import settings

OPENROUTER_URL = "https://openrouter.ai/api/v1/chat/completions"

async def chat_json(system: str, user: str) -> dict:
    if not settings.OPENROUTER_API_KEY:
        raise RuntimeError("OPENROUTER_API_KEY not set")

    headers = {
        "Authorization": f"Bearer {settings.OPENROUTER_API_KEY}",
        "Content-Type": "application/json",
        "HTTP-Referer": settings.OPENROUTER_SITE_URL,
        "X-Title": settings.OPENROUTER_APP_NAME,
    }

    payload = {
        "model": settings.OPENROUTER_MODEL,
        "messages": [
            {"role": "system", "content": system},
            {"role": "user", "content": user},
        ],
        "temperature": 0.4,
    }

    async with httpx.AsyncClient(timeout=120.0) as client:
        r = await client.post(OPENROUTER_URL, headers=headers, json=payload)
        r.raise_for_status()
        data = r.json()

    content = data["choices"][0]["message"]["content"]
    return {"raw": content, "model": settings.OPENROUTER_MODEL}
