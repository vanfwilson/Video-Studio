import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_engine
from app.api_videos import router as video_router
from app.api_youtube import router as youtube_router

def parse_origins(v: str):
    v = v.strip()
    if v == "*":
        return ["*"]
    return [x.strip() for x in v.split(",") if x.strip()]

app = FastAPI(title="Video Studio API", version="1.0.0")

@app.on_event("startup")
def startup():
    init_engine(settings.DATABASE_URL)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)

origins = parse_origins(settings.CORS_ORIGINS)
app.add_middleware(
    CORSMiddleware,
    allow_origins=origins if origins != ["*"] else ["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Routers
app.include_router(video_router)
app.include_router(youtube_router)

# Health
@app.get("/health")
def health():
    return {"ok": True}

# Expose uploads publicly: /uploads/{user}/{file}
# (n8n transcribe needs public URLs)
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")
