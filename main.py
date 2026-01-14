from fastapi import FastAPI
from app.api.video import router as video_router
from app.api.youtube import router as youtube_router

app = FastAPI(
    title="Video Studio Microservice",
    description="Handles video processing, captions, and YouTube publishing",
    version="1.0.0"
)

app.include_router(video_router, prefix="/video", tags=["Video"])
app.include_router(youtube_router, prefix="/youtube", tags=["YouTube"])
