from fastapi import APIRouter, HTTPException, Depends
from sqlalchemy.orm import Session
from typing import List

from app.db import SessionLocal
from app.security import require_user_id
from app.models import Video
from app.services.openrouter import chat_json
import json

router = APIRouter(prefix="/ai", tags=["ai"])

# Supported languages for caption translation
SUPPORTED_LANGUAGES = {
    "en": "English",
    "es": "Spanish",
    "fr": "French",
    "de": "German",
    "it": "Italian",
    "pt": "Portuguese",
    "nl": "Dutch",
    "pl": "Polish",
    "ru": "Russian",
    "ja": "Japanese",
    "ko": "Korean",
    "zh": "Chinese (Simplified)",
    "zh-TW": "Chinese (Traditional)",
    "ar": "Arabic",
    "hi": "Hindi",
    "th": "Thai",
    "vi": "Vietnamese",
    "id": "Indonesian",
    "ms": "Malay",
    "tl": "Filipino/Tagalog",
    "tr": "Turkish",
    "sv": "Swedish",
    "da": "Danish",
    "no": "Norwegian",
    "fi": "Finnish",
    "el": "Greek",
    "he": "Hebrew",
    "cs": "Czech",
    "ro": "Romanian",
    "hu": "Hungarian",
}

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

# ============================================
# CAPTION TRANSLATION
# ============================================

TRANSLATE_SYSTEM = """You are a professional translator specializing in video subtitles/captions.
Translate the following SRT captions accurately while preserving:
- All timing codes exactly as given
- The structure and line breaks
- Natural, conversational language
- Cultural context where appropriate
Return ONLY the translated SRT content, no explanations.
"""

TRANSLATE_PROMPT = """Translate the following SRT captions from {source_lang} to {target_lang}.
Keep all timing codes (like "00:00:01,000 --> 00:00:05,000") exactly the same.
Only translate the text content between timing codes.

SRT CONTENT:
{content}

TRANSLATED SRT:"""

@router.get("/caption-languages")
def get_supported_languages():
    """Return list of supported languages for caption translation."""
    return {
        "languages": [
            {"code": code, "name": name}
            for code, name in SUPPORTED_LANGUAGES.items()
        ]
    }

@router.post("/captions/translate")
async def translate_captions(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    """
    Translate captions to multiple languages using AI.

    Payload:
    {
        "video_id": 123,
        "target_languages": ["es", "fr", "de"],  // list of language codes
        "source_language": "en"  // optional, defaults to "en"
    }

    Returns:
    {
        "ok": true,
        "translations": {
            "es": {"language": "Spanish", "captions": "..."},
            "fr": {"language": "French", "captions": "..."},
            ...
        },
        "model_used": "..."
    }
    """
    video_id = payload.get("video_id")
    target_languages = payload.get("target_languages", [])
    source_language = payload.get("source_language", "en")

    if not video_id:
        raise HTTPException(400, "video_id required")
    if not target_languages:
        raise HTTPException(400, "target_languages required (list of language codes)")

    # Validate languages
    invalid_langs = [l for l in target_languages if l not in SUPPORTED_LANGUAGES]
    if invalid_langs:
        raise HTTPException(400, f"Invalid language codes: {invalid_langs}. Supported: {list(SUPPORTED_LANGUAGES.keys())}")

    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    # Get source captions
    source_captions = None
    if isinstance(v.captions, dict):
        # Multi-language format - try to get source language
        if source_language in v.captions:
            cap_data = v.captions[source_language]
            source_captions = cap_data.get("content") or cap_data.get("srt") or cap_data.get("text")
        elif "en" in v.captions:
            cap_data = v.captions["en"]
            source_captions = cap_data.get("content") or cap_data.get("srt") or cap_data.get("text")
        else:
            # Try legacy format
            source_captions = v.captions.get("srt") or v.captions.get("text") or v.captions.get("content")
    elif isinstance(v.captions, str):
        source_captions = v.captions

    if not source_captions:
        raise HTTPException(400, "No captions available to translate. Run caption generation first.")

    source_lang_name = SUPPORTED_LANGUAGES.get(source_language, "English")
    translations = {}
    model_used = None

    # Translate to each target language
    for lang_code in target_languages:
        if lang_code == source_language:
            continue  # Skip translating to same language

        target_lang_name = SUPPORTED_LANGUAGES[lang_code]

        prompt = TRANSLATE_PROMPT.format(
            source_lang=source_lang_name,
            target_lang=target_lang_name,
            content=source_captions[:30000]  # Limit content size
        )

        res = await chat_json(TRANSLATE_SYSTEM, prompt)
        model_used = res.get("model")

        translated_text = res.get("raw", "").strip()

        translations[lang_code] = {
            "language": target_lang_name,
            "captions": translated_text
        }

    # Update video captions with translations
    existing_captions = v.captions if isinstance(v.captions, dict) else {}

    # Handle legacy format conversion
    if isinstance(v.captions, str) or (isinstance(v.captions, dict) and ("srt" in v.captions or "text" in v.captions)):
        if isinstance(v.captions, str):
            existing_captions = {source_language: {"format": "srt", "content": v.captions}}
        else:
            legacy_content = v.captions.get("srt") or v.captions.get("text") or v.captions.get("content")
            existing_captions = {source_language: {"format": "srt", "content": legacy_content}}

    # Add translations
    for lang_code, trans_data in translations.items():
        existing_captions[lang_code] = {
            "format": "srt",
            "content": trans_data["captions"]
        }

    v.captions = existing_captions
    db.add(v)
    db.commit()

    return {
        "ok": True,
        "translations": translations,
        "languages_added": list(translations.keys()),
        "total_languages": len(existing_captions),
        "model_used": model_used
    }
