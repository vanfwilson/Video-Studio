from fastapi import APIRouter
from app.services.youtube_api import upload_to_youtube

router = APIRouter()

@router.post("/publish")
def publish_video(video_id: int):
    result = upload_to_youtube(video_id)
    return {"youtube_url": result}
