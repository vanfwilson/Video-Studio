import os
import uuid
import shutil
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
        db.add(User(id=user_id))
        db.commit()

def safe_name(name: str) -> str:
    name = name.replace("\\", "_").replace("/", "_")
    return "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", " ")).strip() or "video.mp4"

def public_upload_url(user_id: str, filename: str) -> str:
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/{user_id}/{filename}"

def serialize(v: Video) -> dict:
    caps_str = None
    if isinstance(v.captions, dict):
        caps_str = v.captions.get("srt") or v.captions.get("text")
    return {
        "id": v.id,
        "user_id": v.user_id,
        "original_filename": v.original_filename,
        "storage_path": v.storage_path,
        "status": v.status,
        "transcript": v.transcript,
        "captions": caps_str,
        "title": v.title,
        "description": v.description,
        "tags": v.tags,
        "hashtags": v.hashtags,
        "thumbnail_url": v.thumbnail_url,
        "privacy_status": v.privacy_status,
        "youtube_id": v.youtube_id,
        "youtube_url": v.youtube_url,
        "error_message": v.error_message,
    }

@router.get("")
def list_videos(user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    ensure_user(db, user_id)
    rows = db.query(Video).filter(Video.user_id == user_id).order_by(Video.id.desc()).all()
    return [serialize(v) for v in rows]

@router.get("/{video_id}")
def get_video(video_id: int, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    v = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")
    return serialize(v)

@router.patch("/{video_id}")
def patch_video(video_id: int, payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    v = db.query(Video).filter(Video.id == video_id, Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    allowed = {
        "status", "transcript", "captions", "title", "description", "tags", "hashtags",
        "thumbnail_url", "thumbnail_prompt", "privacy_status", "language", "error_message"
    }
    for k, val in payload.items():
        if k in allowed:
            setattr(v, k, val)

    db.add(v)
    db.commit()
    db.refresh(v)
    return serialize(v)

@router.post("/upload")
async def upload(
    file: UploadFile = File(...),
    user_id: str = Depends(require_user_id),
    db: Session = Depends(db_dep)
):
    ensure_user(db, user_id)
    if not file.filename:
        raise HTTPException(400, "Missing filename")

    os.makedirs(os.path.join(settings.UPLOAD_DIR, user_id), exist_ok=True)
    fname = f"{uuid.uuid4().hex}_{safe_name(file.filename)}"
    local_path = os.path.join(settings.UPLOAD_DIR, user_id, fname)

    with open(local_path, "wb") as f:
        shutil.copyfileobj(file.file, f)

    v = Video(
        user_id=user_id,
        original_filename=safe_name(file.filename),
        storage_path=public_upload_url(user_id, fname),
        status="ready",
        language="en",
        privacy_status="private",
    )
    db.add(v)
    db.commit()
    db.refresh(v)
    return serialize(v)

@router.post("/ingest")
def ingest(payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    ensure_user(db, user_id)
    url = (payload.get("video_url") or "").strip()
    if not url:
        raise HTTPException(400, "video_url required")

    filename = safe_name(payload.get("filename") or "ingested.mp4")

    v = Video(
        user_id=user_id,
        original_filename=filename,
        storage_path=url,
        status="ready",
        language="en",
        privacy_status="private",
    )
    db.add(v)
    db.commit()
    db.refresh(v)

    db.add(VideoIngestRequest(
        user_id=user_id,
        provider="url",
        source_path=url,
        source_file_name=filename,
        status="done",
        video_id=v.id
    ))
    db.commit()

    return serialize(v)

@router.post("/caption")
async def caption(payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    """
    Calls n8n:
      POST N8N_TRANSCRIBE_URL
      Content-Type: application/x-www-form-urlencoded
      params: video_url, language_code
    Response: { "text": "...", "srt": "..." }
    """
    ensure_user(db, user_id)

    vid = payload.get("video_id")
    if not vid:
        raise HTTPException(400, "video_id required")

    language_code = payload.get("language_code") or settings.DEFAULT_LANGUAGE_CODE

    v = db.query(Video).filter(Video.id == int(vid), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    # n8n needs a public URL
    video_url = v.storage_path
    if not video_url:
        raise HTTPException(400, "Video storage_path is empty")

    v.status = "captioning"
    db.add(v)
    db.commit()

    try:
        res = await transcribe_via_n8n(video_url=video_url, language_code=language_code)
    except Exception as e:
        v.status = "error"
        v.error_message = f"Transcribe failed: {e}"
        db.add(v)
        db.commit()
        raise HTTPException(502, v.error_message)

    srt = res.get("srt")
    text = res.get("text")

    # Store in DB (JSONB)
    if srt:
        v.captions = {"format": "srt", "srt": srt}
    elif text:
        v.captions = {"format": "text", "text": text}
    else:
        v.captions = None

    v.transcript = text or v.transcript
    v.status = "metadata_ready"
    db.add(v)
    db.commit()
    db.refresh(v)

    # Optional: write an .srt file so you can see it on disk
    if srt:
        try:
            out_dir = os.path.join(settings.UPLOAD_DIR, user_id)
            os.makedirs(out_dir, exist_ok=True)
            srt_path = os.path.join(out_dir, f"video_{v.id}.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt)
        except Exception:
            pass

    return {
        "captions_format": "srt" if srt else "text",
        "captions": srt if srt else (text or "")
    }

