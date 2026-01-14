from fastapi import APIRouter, HTTPException
from app.models.db import SessionLocal
from app.models.video import Video
import requests

router = APIRouter()

N8N_CAPTION_URL = "http://72.60.225.136:8001/transcribe"

@router.post("/caption")
def request_caption(video_id: int):
    db = SessionLocal()
    video = db.query(Video).filter(Video.id == video_id).first()

    if not video:
        raise HTTPException(status_code=404, detail="Video not found")

    video_url = video.storage_path
    if not video_url:
        raise HTTPException(status_code=400, detail="Video URL not found")

    try:
        response = requests.post(
            N8N_CAPTION_URL,
            data={
                "video_url": video_url,
                "language_code": "en"
            },
            headers={
                "Content-Type": "application/x-www-form-urlencoded"
            }
        )
        response.raise_for_status()
        result = response.json()

        srt = result.get("srt")
        text = result.get("text")

        if not srt and not text:
            raise HTTPException(status_code=502, detail="No captions returned from webhook.")

        # Update DB
        video.captions = srt or None
        video.transcript = text or None
        db.commit()

        return {
            "status": "success",
            "captions_format": "srt" if srt else "text",
            "captions": srt if srt else text
        }

    except requests.RequestException as e:
        raise HTTPException(status_code=500, detail=f"Webhook error: {str(e)}")
