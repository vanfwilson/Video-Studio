import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_engine
from app.api_videos import router as video_router
from app.api_youtube import router as youtube_router

app = FastAPI(title="Video Studio API", version="1.0.0")

@app.on_event("startup")
def startup():
    init_engine(settings.DATABASE_URL)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip()]
app.add_middleware(CORSMiddleware, allow_origins=origins, allow_credentials=True, allow_methods=["*"], allow_headers=["*"])

app.include_router(video_router)
app.include_router(youtube_router)

@app.get("/health")
def health():
    return {"ok": True}

# public files for n8n: /uploads/<user_id>/<file>
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
