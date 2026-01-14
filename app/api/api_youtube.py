import os
import tempfile
import httpx

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.security import require_user_id
from app.models import Video
from app.services.youtube import (
    create_auth_url, exchange_code, youtube_connected, upload_video_to_youtube
)

router = APIRouter(prefix="/youtube", tags=["youtube"])

def db_dep():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()

@router.get("/status")
def status(user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    ok, row = youtube_connected(db, user_id)
    account = None
    if row:
        account = {
            "platform": "youtube",
            "account_name": row.account_name,
            "channel_id": row.channel_id,
            "profile_image_url": row.profile_image_url,
            "is_active": row.is_active,
        }
    return {"connected": ok, "account": account}

@router.post("/auth/start")
def auth_start(user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    try:
        url = create_auth_url(db, user_id)
    except Exception as e:
        raise HTTPException(500, f"YouTube auth start failed: {e}")
    return {"auth_url": url}

@router.post("/auth/callback")
def auth_callback(payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    code = payload.get("code")
    state = payload.get("state")
    if not code or not state:
        raise HTTPException(400, "code and state required")
    try:
        exchange_code(db, user_id=user_id, code=code, state=state)
        return {"ok": True}
    except Exception as e:
        raise HTTPException(400, f"OAuth exchange failed: {e}")

@router.post("/publish")
def publish(payload: dict, user_id: str = Depends(require_user_id), db: Session = Depends(db_dep)):
    video_id = payload.get("video_id")
    if not video_id:
        raise HTTPException(400, "video_id required")

    v = db.query(Video).filter(Video.id == int(video_id), Video.user_id == user_id).first()
    if not v:
        raise HTTPException(404, "Video not found")

    title = payload.get("title") or v.title or v.original_filename
    description = payload.get("description") or v.description or ""
    tags_str = payload.get("tags") or v.tags or ""
    privacy_status = payload.get("privacy_status") or v.privacy_status or "private"

    tags = [t.strip() for t in tags_str.split(",") if t.strip()]

    # Need a local file to upload. If storage_path is a public URL, download it first.
    local_path = None
    try:
        if v.storage_path.startswith("http://") or v.storage_path.startswith("https://"):
            # download to temp
            with tempfile.NamedTemporaryFile(delete=False, suffix=".mp4") as tmp:
                local_path = tmp.name
            with httpx.stream("GET", v.storage_path, timeout=300.0) as r:
                r.raise_for_status()
                with open(local_path, "wb") as f:
                    for chunk in r.iter_bytes():
                        f.write(chunk)
        else:
            local_path = v.storage_path

        v.status = "processing"
        db.add(v); db.commit()

        res = upload_video_to_youtube(
            db=db,
            user_id=user_id,
            file_path=local_path,
            title=title,
            description=description,
            tags=tags,
            privacy_status=privacy_status,
        )

        v.youtube_id = res.get("youtube_id")
        v.youtube_url = res.get("youtube_url")
        v.status = "published"
        db.add(v); db.commit()
        db.refresh(v)

        return {"youtube_id": v.youtube_id, "youtube_url": v.youtube_url, "status": v.status}
    except Exception as e:
        v.status = "error"
        v.error_message = f"Publish failed: {e}"
        db.add(v); db.commit()
        raise HTTPException(500, v.error_message)
    finally:
        if local_path and (local_path.startswith("/tmp") or "tmp" in local_path):
            try:
                os.remove(local_path)
            except Exception:
                pass
