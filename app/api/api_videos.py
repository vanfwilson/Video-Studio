import os
import pathlib
import shutil
import uuid
import httpx

from fastapi import APIRouter, UploadFile, File, HTTPException, Depends
from sqlalchemy.orm import Session

from app.config import settings
from app.db import SessionLocal
from app.security import require_user_id
from app.models import User, Video, VideoIngestRequest
from app.services.n8n import transcribe_via_n8n

router = APIRouter(prefix="/video", tags=["video"])

def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

def ensure_user(db: Session, user_id: str):
    u = db.query(User).filter(User.id == user_id).first()
    if not u:
        u = User(id=user_id)
        db.add(u)
        db.commit()

def _safe_filename(name: str) -> str:
    name = name.replace("\\", "_").replace("/", "_")
    return "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", " ")).strip() or "video.mp4"

def _public_upload_url(user_id: str, rel_path: str) -> str:
    # exposed by backend at /uploads/...
    base = settings.PUBLIC_BASE_URL.rstrip("/")
    return f"{base}/uploads/{user_id}/{rel_path}"

@router.get("")
def list_videos(user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    ensure_user(db, user_id)
    vids = db.query(Video).filter(Video.user_id == user_id).order_by(Video.id.desc()).all()
    return [serialize_video(v) for v in vids]

@router.get("/{video_id}")
def get_video(video_id: int, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    v = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    return serialize_video(v)

@router.patch("/{video_id}")
def patch_video(video_id: int, payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    v = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    allowed = {
        "status","transcript","captions","title","description","tags","hashtags",
        "thumbnail_url","thumbnail_prompt","privacy_status","language",
        "trim_start_ms","trim_end_ms","start_sec","end_sec","error_message"
    }
    for k, val in payload.items():
        if k in allowed:
            setattr(v, k, val)

    db.add(v)
    db.commit()
    db.refresh(v)
    return serialize_video(v)

@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep),
):
    ensure_user(db, user_id)

    if not file.filename:
        raise HTTPException(400, "Missing filename")

    safe = _safe_filename(file.filename)
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)

    unique = f"{uuid.uuid4().hex}_{safe}"
    dst_path = os.path.join(user_dir, unique)

    # write stream to disk
    with open(dst_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    rel = unique
    public_url = _public_upload_url(user_id, rel)

    v = Video(
        user_id=user_id,
        original_filename=safe,
        storage_path=public_url,
        status="ready",
        language="en",
        privacy_status="private",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return serialize_video(v)

@router.post("/ingest")
def ingest_video(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep),
):
    ensure_user(db, user_id)
    video_url = (payload.get("video_url") or "").strip()
    filename = (payload.get("filename") or "ingested.mp4").strip()
    if not video_url:
        raise HTTPException(400, "video_url required")

    v = Video(
        user_id=user_id,
        original_filename=_safe_filename(filename),
        storage_path=video_url,
        status="ready",
        language="en",
        privacy_status="private",
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    req = VideoIngestRequest(
        user_id=user_id,
        provider="url",
        source_path=video_url,
        source_file_name=v.original_filename,
        status="done",
        video_id=v.id,
    )
    db.add(req)
    db.commit()

    return serialize_video(v)

@router.post("/caption")
async def caption_video(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep),
):
    video_id = payload.get("video_id")
    language_code = payload.get("language_code") or settings.DEFAULT_LANGUAGE_CODE
    if not video_id:
        raise HTTPException(400, "video_id required")

    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    v.status = "captioning"
    db.add(v)
    db.commit()

    # n8n expects public URL
    video_url = v.storage_path
    try:
        res = await transcribe_via_n8n(video_url=video_url, language_code=language_code)
    except Exception as e:
        v.status = "error"
        v.error_message = f"Caption webhook failed: {e}"
        db.add(v); db.commit()
        raise HTTPException(502, v.error_message)

    text = res.get("text")
    srt = res.get("srt")

    # Prefer srt if available; store in captions jsonb for compatibility
    if srt:
        v.captions = {"format": "srt", "srt": srt}
    elif text:
        v.captions = {"format": "text", "text": text}
    else:
        v.captions = None

    v.transcript = text or v.transcript
    v.status = "metadata_ready" if v.captions else "ready"
    db.add(v)
    db.commit()
    db.refresh(v)

    return {
        "captions_format": "srt" if srt else "text",
        "captions": srt if srt else (text or "")
    }

def serialize_video(v: Video) -> dict:
    # Normalize captions: if stored as jsonb, still return a convenient string field as well
    captions_str = None
    if isinstance(v.captions, dict):
        captions_str = v.captions.get("srt") or v.captions.get("text")
    return {
        "id": v.id,
        "user_id": v.user_id,
        "original_filename": v.original_filename,
        "storage_path": v.storage_path,
        "status": v.status,
        "transcript": v.transcript,
        "captions": captions_str,
        "title": v.title,
        "description": v.description,
        "tags": v.tags,
        "hashtags": v.hashtags,
        "thumbnail_url": v.thumbnail_url,
        "language": v.language,
        "privacy_status": v.privacy_status,
        "youtube_id": v.youtube_id,
        "youtube_url": v.youtube_url,
        "error_message": v.error_message,
        "created_at": getattr(v, "created_at", None),
        "updated_at": getattr(v, "updated_at", None),
    }
