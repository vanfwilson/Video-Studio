import os
import uuid
import shutil
from datetime import datetime
from typing import Optional, List
from fastapi import APIRouter, UploadFile, File, HTTPException, Depends, BackgroundTasks
from sqlalchemy.orm import Session

from app.config import settings
from app.db import get_db
from app.security import require_user_id
from app.models import User, Video, VideoIngestRequest, PublishTransaction, ConfidentialityCheck
from app.services.n8n import transcribe_via_n8n
from app.services.metadata import generate_metadata
from app.services.confidentiality import run_confidentiality_check

router = APIRouter(prefix="/video", tags=["video"])


def ensure_user(db: Session, user_id: str):
    """Create user if doesn't exist."""
    user = db.query(User).filter(User.id == user_id).first()
    if not user:
        db.add(User(id=user_id))
        db.commit()


def safe_filename(name: str) -> str:
    """Sanitize filename for storage."""
    name = name.replace("\\", "_").replace("/", "_")
    return "".join(ch for ch in name if ch.isalnum() or ch in ("-", "_", ".", " ")).strip() or "video.mp4"


def public_url(user_id: str, filename: str) -> str:
    """Generate public URL for video file."""
    return f"{settings.PUBLIC_BASE_URL.rstrip('/')}/uploads/{user_id}/{filename}"


def serialize_video(v: Video) -> dict:
    """Serialize Video model to response dict."""
    # Extract caption text from JSONB
    captions_text = None
    if isinstance(v.captions, dict):
        captions_text = v.captions.get("srt") or v.captions.get("text")
    elif isinstance(v.captions, str):
        captions_text = v.captions
    
    return {
        "id": v.id,
        "user_id": v.user_id,
        "original_filename": v.original_filename,
        "storage_path": v.storage_path,
        "file_size": v.file_size,
        "mime_type": v.mime_type,
        "duration_ms": v.duration_ms,
        "status": v.status,
        "error_message": v.error_message,
        "transcript": v.transcript,
        "captions": captions_text,
        "language": v.language,
        "ai_summary": v.ai_summary,
        "title": v.title,
        "description": v.description,
        "tags": v.tags,
        "hashtags": v.hashtags,
        "thumbnail_prompt": v.thumbnail_prompt,
        "thumbnail_url": v.thumbnail_url,
        "privacy_status": v.privacy_status,
        "category": v.category,
        "youtube_id": v.youtube_id,
        "youtube_url": v.youtube_url,
        "youtube_channel_id": v.youtube_channel_id,
        "published_at": v.published_at.isoformat() if v.published_at else None,
        "confidentiality_status": v.confidentiality_status,
        "confidentiality_issues": v.confidentiality_issues or [],
        "created_at": v.created_at.isoformat() if v.created_at else None,
        "updated_at": v.updated_at.isoformat() if v.updated_at else None,
    }


@router.get("")
def list_videos(
    status: Optional[str] = None,
    limit: int = 50,
    offset: int = 0,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """List all videos for the user."""
    ensure_user(db, user_id)
    
    query = db.query(Video).filter(Video.user_id == user_id)
    if status:
        query = query.filter(Video.status == status)
    
    videos = query.order_by(Video.id.desc()).offset(offset).limit(limit).all()
    return [serialize_video(v) for v in videos]


@router.get("/{video_id}")
def get_video(
    video_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Get a single video by ID."""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    return serialize_video(video)


@router.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Upload a new video file."""
    ensure_user(db, user_id)
    
    if not file.filename:
        raise HTTPException(400, "Missing filename")
    
    # Create user directory
    user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
    os.makedirs(user_dir, exist_ok=True)
    
    # Generate unique filename
    safe_name = safe_filename(file.filename)
    unique_name = f"{uuid.uuid4().hex}_{safe_name}"
    file_path = os.path.join(user_dir, unique_name)
    
    # Save file
    file_size = 0
    with open(file_path, "wb") as f:
        while chunk := await file.read(1024 * 1024):  # 1MB chunks
            f.write(chunk)
            file_size += len(chunk)
    
    # Create video record
    video = Video(
        user_id=user_id,
        original_filename=safe_name,
        storage_path=public_url(user_id, unique_name),
        file_size=file_size,
        mime_type=file.content_type or "video/mp4",
        status="ready",
        language="en",
        privacy_status="private"
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    return serialize_video(video)


@router.post("/ingest")
def ingest_from_url(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Create video from existing URL (for cloud imports)."""
    ensure_user(db, user_id)
    
    url = (payload.get("video_url") or "").strip()
    if not url:
        raise HTTPException(400, "video_url required")
    
    filename = safe_filename(payload.get("filename") or "ingested.mp4")
    
    video = Video(
        user_id=user_id,
        original_filename=filename,
        storage_path=url,
        status="ready",
        language="en",
        privacy_status="private"
    )
    db.add(video)
    db.commit()
    db.refresh(video)
    
    # Create ingest record
    db.add(VideoIngestRequest(
        user_id=user_id,
        provider="url",
        source_path=url,
        source_file_name=filename,
        status="done",
        video_id=video.id
    ))
    db.commit()
    
    return serialize_video(video)


@router.patch("/{video_id}")
def update_video(
    video_id: int,
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Update video metadata."""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Allowed fields to update
    allowed = {
        "status", "transcript", "captions", "title", "description", 
        "tags", "hashtags", "thumbnail_url", "thumbnail_prompt", 
        "privacy_status", "language", "error_message", "category"
    }
    
    for key, value in payload.items():
        if key in allowed:
            # Special handling for captions
            if key == "captions" and isinstance(value, str):
                video.captions = {"format": "text", "text": value}
            else:
                setattr(video, key, value)
    
    db.commit()
    db.refresh(video)
    
    return serialize_video(video)


@router.delete("/{video_id}")
def delete_video(
    video_id: int,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Delete a video."""
    video = db.query(Video).filter(
        Video.id == video_id,
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Try to delete file if it's local
    if video.storage_path and "/uploads/" in video.storage_path:
        try:
            parts = video.storage_path.split("/uploads/")
            if len(parts) > 1:
                local_path = os.path.join(settings.UPLOAD_DIR, parts[1])
                if os.path.exists(local_path):
                    os.remove(local_path)
        except Exception:
            pass  # File deletion is best-effort
    
    db.delete(video)
    db.commit()
    
    return {"ok": True, "video_id": video_id}


@router.post("/caption")
async def request_captions(
    payload: dict,
    background_tasks: BackgroundTasks,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Request AI transcription via n8n."""
    ensure_user(db, user_id)
    
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")
    
    language_code = payload.get("language_code") or settings.DEFAULT_LANGUAGE_CODE
    
    video = db.query(Video).filter(
        Video.id == int(video_id),
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    if not video.storage_path:
        raise HTTPException(400, "Video storage_path is empty")
    
    # Update status
    video.status = "captioning"
    db.commit()
    
    # Create transaction record
    transaction = PublishTransaction(
        video_id=video.id,
        user_id=user_id,
        action="transcribe",
        request_payload={
            "video_url": video.storage_path,
            "language_code": language_code
        }
    )
    db.add(transaction)
    db.commit()
    
    # Call n8n
    try:
        result = await transcribe_via_n8n(
            video_url=video.storage_path,
            language_code=language_code
        )
    except Exception as e:
        video.status = "error"
        video.error_message = f"Transcription failed: {str(e)}"
        transaction.status = "failed"
        transaction.error_message = str(e)
        transaction.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(502, video.error_message)
    
    # Process result
    srt = result.get("srt")
    text = result.get("text")
    
    if srt:
        video.captions = {"format": "srt", "srt": srt}
    elif text:
        video.captions = {"format": "text", "text": text}
    
    video.transcript = text or video.transcript
    video.status = "metadata_ready"
    
    transaction.status = "success"
    transaction.response_payload = result
    transaction.completed_at = datetime.utcnow()
    
    db.commit()
    
    # Write SRT file to disk
    if srt:
        try:
            user_dir = os.path.join(settings.UPLOAD_DIR, user_id)
            os.makedirs(user_dir, exist_ok=True)
            srt_path = os.path.join(user_dir, f"video_{video.id}.srt")
            with open(srt_path, "w", encoding="utf-8") as f:
                f.write(srt)
        except Exception:
            pass
    
    return {
        "captions_format": "srt" if srt else "text",
        "captions": srt if srt else (text or "")
    }


@router.post("/metadata/generate")
async def generate_video_metadata(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Generate AI metadata from transcript."""
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")
    
    video = db.query(Video).filter(
        Video.id == int(video_id),
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Get content to analyze
    content = None
    if isinstance(video.captions, dict):
        content = video.captions.get("srt") or video.captions.get("text")
    content = content or video.transcript
    
    if not content:
        raise HTTPException(400, "No captions/transcript available. Run caption first.")
    
    # Create transaction
    transaction = PublishTransaction(
        video_id=video.id,
        user_id=user_id,
        action="metadata",
        request_payload={"video_id": video_id}
    )
    db.add(transaction)
    db.commit()
    
    try:
        metadata, model_used = await generate_metadata(content)
    except Exception as e:
        transaction.status = "failed"
        transaction.error_message = str(e)
        transaction.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(502, f"Metadata generation failed: {str(e)}")
    
    # Update video
    video.ai_summary = metadata.get("ai_summary") or video.ai_summary
    video.title = metadata.get("title") or video.title
    video.description = metadata.get("description") or video.description
    video.tags = metadata.get("tags") or video.tags
    video.hashtags = metadata.get("hashtags") or video.hashtags
    video.thumbnail_prompt = metadata.get("thumbnail_prompt") or video.thumbnail_prompt
    
    transaction.status = "success"
    transaction.response_payload = metadata
    transaction.completed_at = datetime.utcnow()
    
    db.commit()
    db.refresh(video)
    
    return {
        "ai_summary": video.ai_summary,
        "title": video.title,
        "description": video.description,
        "tags": video.tags,
        "hashtags": video.hashtags,
        "thumbnail_prompt": video.thumbnail_prompt,
        "model_used": model_used
    }


@router.post("/confidentiality/check")
async def check_confidentiality(
    payload: dict,
    user_id: str = Depends(require_user_id),
    db: Session = Depends(get_db)
):
    """Run confidentiality check on video transcript."""
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")
    
    video = db.query(Video).filter(
        Video.id == int(video_id),
        Video.user_id == user_id
    ).first()
    
    if not video:
        raise HTTPException(404, "Video not found")
    
    # Get transcript
    transcript = video.transcript
    if not transcript and isinstance(video.captions, dict):
        transcript = video.captions.get("text") or video.captions.get("srt")
    
    if not transcript:
        raise HTTPException(400, "No transcript available for confidentiality check")
    
    # Create transaction
    transaction = PublishTransaction(
        video_id=video.id,
        user_id=user_id,
        action="confidentiality",
        request_payload={"video_id": video_id}
    )
    db.add(transaction)
    db.commit()
    
    try:
        result, model_used = await run_confidentiality_check(transcript)
    except Exception as e:
        transaction.status = "failed"
        transaction.error_message = str(e)
        transaction.completed_at = datetime.utcnow()
        db.commit()
        raise HTTPException(502, f"Confidentiality check failed: {str(e)}")
    
    # Save check record
    check = ConfidentialityCheck(
        video_id=video.id,
        user_id=user_id,
        overall_status=result.get("overall_status", "pass"),
        summary=result.get("summary"),
        counts=result.get("counts", {}),
        segments=result.get("segments", []),
        model_used=model_used
    )
    db.add(check)
    
    # Update video
    video.confidentiality_status = result.get("overall_status", "pass")
    video.confidentiality_issues = result.get("segments", [])
    video.last_confidentiality_check_at = datetime.utcnow()
    
    transaction.status = "success"
    transaction.response_payload = result
    transaction.completed_at = datetime.utcnow()
    
    db.commit()
    
    return {
        "overall_status": result.get("overall_status"),
        "summary": result.get("summary"),
        "counts": result.get("counts"),
        "segments": result.get("segments"),
        "model_used": model_used
    }
