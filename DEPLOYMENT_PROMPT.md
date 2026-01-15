# Video Studio - Deployment Prompt for Claude Code on Linux VPS

Use this prompt with Claude Code on your Linux server to deploy the Video Studio application in your Docker stack with Traefik and Portainer.

---

## Deployment Prompt

```
Deploy the Video Studio application from https://github.com/vanfwilson/Video-Studio
(branch: claude/video-publishing-spa-NWGra) as a Docker stack on this Linux VPS.

Requirements:
- Traefik reverse proxy with Cloudflare SSL
- PostgreSQL 16 database
- FastAPI backend on /api/* routes
- React frontend served by nginx
- Domain: video-studio.askstephen.ai (or your domain)
- Portainer compatible deployment

Steps to perform:

1. CLONE REPOSITORY
   - Clone from GitHub to /opt/video-studio or appropriate location
   - Checkout branch: claude/video-publishing-spa-NWGra

2. CONFIGURE ENVIRONMENT
   - Copy .env.example to .env
   - Set the following variables:
     * POSTGRES_PASSWORD: Generate a secure password
     * PUBLIC_BASE_URL: https://video-studio.askstephen.ai
     * N8N_TRANSCRIBE_URL: (user's n8n transcription webhook URL)
     * N8N_PUBLISH_URL: (user's n8n publish webhook URL)
     * OPENROUTER_API_KEY: (user's OpenRouter API key)
     * YOUTUBE_CLIENT_ID: (from Google Cloud Console)
     * YOUTUBE_CLIENT_SECRET: (from Google Cloud Console)
     * YOUTUBE_REDIRECT_URI: https://video-studio.askstephen.ai/oauth/youtube/callback

3. NETWORK SETUP
   - Ensure traefik-network exists: docker network create traefik-network
   - Or use existing external Traefik network name

4. TRAEFIK CONFIGURATION
   The docker-compose.yml includes Traefik labels for:
   - video-studio.askstephen.ai → React frontend (port 80)
   - video-studio.askstephen.ai/api/* → FastAPI backend (port 8080, strip /api prefix)
   - video-studio.askstephen.ai/uploads/* → Static file serving
   - video-studio.askstephen.ai/oauth/* → OAuth callbacks

5. DNS CONFIGURATION
   - Create A record or CNAME for video-studio.askstephen.ai pointing to VPS IP
   - Enable Cloudflare proxy (orange cloud) for CDN and SSL

6. DEPLOY STACK
   cd /opt/video-studio
   docker-compose up -d --build

7. VERIFY DEPLOYMENT
   - Check container health: docker-compose ps
   - View logs: docker-compose logs -f
   - Test health endpoint: curl https://video-studio.askstephen.ai/api/health
   - Access frontend: https://video-studio.askstephen.ai

8. DATABASE INITIALIZATION
   The init.sql script runs automatically on first start, creating all tables.
   If needed to reset: docker-compose down -v && docker-compose up -d

9. PORTAINER INTEGRATION (optional)
   Import the stack in Portainer using the docker-compose.yml file
   Set environment variables in the Portainer UI

Notes:
- The backend exposes port 8080 internally
- The frontend nginx serves on port 80 internally
- PostgreSQL uses port 5432 internally (not exposed externally)
- Video uploads are stored in the video_studio_uploads volume
- Database data persists in video_studio_db_data volume

Troubleshooting:
- If containers fail to start, check logs: docker-compose logs [service-name]
- Verify Traefik network connectivity
- Ensure Cloudflare SSL mode is "Full" or "Full (strict)"
- Check that ports 80/443 are not blocked by firewall
```

---

## Required External Services Setup

### n8n Workflow Setup

Your n8n instance needs two webhook workflows:

1. **Transcription Webhook** (`/webhook/transcribe`)
   - Receives: `video_url`, `language_code` (form-encoded)
   - Uses AssemblyAI, Whisper, or similar service
   - Returns: `{"text": "transcript", "srt": "SRT content"}`

2. **Publish Webhook** (`/webhook/publish`)
   - Receives: JSON with video details, title, description, tags, etc.
   - Uses YouTube Data API v3
   - Returns: `{"youtube_id": "xxx", "youtube_url": "https://youtube.com/watch?v=xxx"}`

### YouTube OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create project or select existing
3. Enable YouTube Data API v3
4. Go to Credentials → Create Credentials → OAuth 2.0 Client ID
5. Application type: Web application
6. Authorized redirect URIs: `https://video-studio.askstephen.ai/oauth/youtube/callback`
7. Copy Client ID and Client Secret to .env

### OpenRouter API

1. Go to [OpenRouter](https://openrouter.ai)
2. Create an account and get API key
3. Add to .env as OPENROUTER_API_KEY

---

## File Structure After Deployment

```
/opt/video-studio/
├── .env                     # Environment variables (create from .env.example)
├── .env.example             # Template for environment variables
├── README.md                # Documentation
├── docker-compose.yml       # Docker stack definition
├── backend/
│   ├── Dockerfile          # Python FastAPI container
│   ├── init.sql            # Database schema
│   ├── requirements.txt    # Python dependencies
│   └── app/                # FastAPI application
│       ├── main.py
│       ├── config.py
│       ├── db.py
│       ├── models.py
│       ├── security.py
│       ├── api_videos.py
│       ├── api_youtube.py
│       └── services/
│           ├── n8n.py
│           ├── openrouter.py
│           ├── metadata.py
│           ├── confidentiality.py
│           └── youtube.py
└── frontend/
    ├── Dockerfile          # Node + nginx container
    ├── nginx.conf          # nginx configuration for SPA
    ├── package.json        # Node dependencies
    └── src/                # React application
        ├── main.tsx
        ├── App.tsx
        ├── types.ts
        ├── api/
        │   └── videoApi.ts
        ├── components/
        │   ├── Layout.tsx
        │   └── ui.tsx
        └── pages/
            ├── Dashboard.tsx
            ├── UploadPage.tsx
            ├── VideoEditor.tsx
            └── YouTubeCallback.tsx
```

---

## Quick Commands Reference

```bash
# Deploy
cd /opt/video-studio
docker-compose up -d --build

# View logs
docker-compose logs -f

# Restart services
docker-compose restart

# Stop everything
docker-compose down

# Reset database (WARNING: deletes all data)
docker-compose down -v
docker-compose up -d

# Update from GitHub
git pull origin claude/video-publishing-spa-NWGra
docker-compose up -d --build

# Check container status
docker-compose ps

# Enter container shell
docker-compose exec video-studio-api bash
docker-compose exec video-studio-web sh
```

---

## API Endpoints Summary

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/video | List videos |
| GET | /api/video/{id} | Get video |
| POST | /api/video/upload | Upload video |
| POST | /api/video/ingest | Ingest from URL |
| PATCH | /api/video/{id} | Update video |
| DELETE | /api/video/{id} | Delete video |
| POST | /api/video/caption | Request transcription |
| POST | /api/video/metadata/generate | Generate AI metadata |
| POST | /api/video/confidentiality/check | Check for PII |
| GET | /api/youtube/status | YouTube connection status |
| POST | /api/youtube/auth/start | Start OAuth flow |
| POST | /api/youtube/auth/callback | OAuth callback |
| POST | /api/youtube/publish | Publish to YouTube |
| DELETE | /api/youtube/disconnect | Disconnect YouTube |
