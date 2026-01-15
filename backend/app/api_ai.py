from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.security import require_user_id
from app.models import Video
from app.services.openrouter import chat_json
import json

router = APIRouter(prefix="/api/video", tags=["ai"])

def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

SYSTEM = """You generate YouTube-ready assets from transcripts.
Return STRICT JSON only. No markdown.
"""

USER_TMPL = """Using the transcript/captions below, generate:
- ai_summary (3-6 bullets)
- title (<= 70 chars)
- description (structured, with CTA, 1-3 short paragraphs)
- tags (comma-separated)
- hashtags (space-separated, include 3-8)
- thumbnail_prompt (short, descriptive, no copyrighted characters)
Return JSON:
{
 "ai_summary": "...",
 "title": "...",
 "description": "...",
 "tags": "...",
 "hashtags": "...",
 "thumbnail_prompt": "..."
}
INPUT:
{content}
"""

def _extract_json(raw: str) -> dict:
    s = raw.find("{"); e = raw.rfind("}")
    if s == -1 or e == -1 or e <= s:
        raise ValueError("Model did not return JSON")
    return json.loads(raw[s:e+1])

@router.post("/metadata/generate")
async def generate_metadata(payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")

    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    content = None
    if isinstance(v.captions, dict):
        content = v.captions.get("srt") or v.captions.get("text")
    content = content or v.transcript
    if not content:
        raise HTTPException(400, "No captions/transcript available. Run caption first.")

    res = await chat_json(SYSTEM, USER_TMPL.format(content=content[:20000]))
    obj = _extract_json(res["raw"])

    v.ai_summary = obj.get("ai_summary") or v.ai_summary
    v.title = obj.get("title") or v.title
    v.description = obj.get("description") or v.description
    v.tags = obj.get("tags") or v.tags
    v.hashtags = obj.get("hashtags") or v.hashtags
    v.thumbnail_prompt = obj.get("thumbnail_prompt") or v.thumbnail_prompt

    db.add(v)
    db.commit()
    db.refresh(v)

    return {
        "ai_summary": v.ai_summary,
        "title": v.title,
        "description": v.description,
        "tags": v.tags,
        "hashtags": v.hashtags,
        "thumbnail_prompt": v.thumbnail_prompt,
        "model_used": res.get("model"),
    }
