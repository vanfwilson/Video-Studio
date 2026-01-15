import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_engine
from app.api_videos import router as video_router
from app.api_ai import router as ai_router
from app.api_publish import router as publish_router

STATIC_DIR = os.path.join(os.path.dirname(__file__), "static")

app = FastAPI(title="Video Studio", version="1.0.0")

@app.on_event("startup")
def startup():
    init_engine(settings.DATABASE_URL)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)
    os.makedirs(STATIC_DIR, exist_ok=True)

origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip()]
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# API routers
app.include_router(video_router)
app.include_router(ai_router)
app.include_router(publish_router)

@app.get("/api/health")
def health():
    return {"ok": True}

# Public uploads for n8n (video_url)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")

# Serve SPA LAST (so /api and /uploads match first)
app.mount("/", StaticFiles(directory=STATIC_DIR, html=True), name="spa")
