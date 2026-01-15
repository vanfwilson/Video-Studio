"""
Video Studio API
================
FastAPI backend for video publishing to YouTube with AI-powered
transcription, metadata generation, and confidentiality checking.

Designed for Pick One Strategy and CoachStephen.AI content publishing.
"""
import os
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles

from app.config import settings
from app.db import init_engine
from app.api_videos import router as video_router
from app.api_youtube import router as youtube_router

# Create FastAPI app
app = FastAPI(
    title="Video Studio API",
    description="Video publishing platform with AI-powered transcription and YouTube integration",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc"
)


@app.on_event("startup")
def startup():
    """Initialize database and create directories."""
    init_engine(settings.DATABASE_URL)
    os.makedirs(settings.UPLOAD_DIR, exist_ok=True)


# CORS Configuration
origins = ["*"] if settings.CORS_ORIGINS.strip() == "*" else [
    x.strip() for x in settings.CORS_ORIGINS.split(",") if x.strip()
]

app.add_middleware(
    CORSMiddleware,
    allow_origins=origins,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Include API routers
app.include_router(video_router)
app.include_router(youtube_router)


@app.get("/health")
def health_check():
    """Health check endpoint for container orchestration."""
    return {
        "status": "healthy",
        "service": "video-studio-api",
        "version": "1.0.0"
    }


@app.get("/")
def root():
    """Root endpoint with API info."""
    return {
        "name": "Video Studio API",
        "version": "1.0.0",
        "docs": "/docs",
        "health": "/health"
    }


# Mount uploads directory for public video access
# This allows n8n to download videos for processing
app.mount("/uploads", StaticFiles(directory=settings.UPLOAD_DIR), name="uploads")


# OAuth callback page (serves simple HTML for redirect handling)
OAUTH_SUCCESS_HTML = """
<!DOCTYPE html>
<html>
<head><title>YouTube Connected</title></head>
<body>
<h1>YouTube Connected Successfully!</h1>
<p>You can close this window and return to Video Studio.</p>
<script>
setTimeout(() => { window.close(); }, 3000);
</script>
</body>
</html>
"""

OAUTH_ERROR_HTML = """
<!DOCTYPE html>
<html>
<head><title>Connection Failed</title></head>
<body>
<h1>Connection Failed</h1>
<p>Error: {message}</p>
<p>Please try again.</p>
</body>
</html>
"""


@app.get("/oauth/youtube/success")
def oauth_success(channel: str = ""):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=OAUTH_SUCCESS_HTML)


@app.get("/oauth/youtube/error")
def oauth_error(message: str = "Unknown error"):
    from fastapi.responses import HTMLResponse
    return HTMLResponse(content=OAUTH_ERROR_HTML.format(message=message))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8080)
