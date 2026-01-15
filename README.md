# Video Studio

AI-powered video publishing platform for YouTube with automated transcription, metadata generation, and confidentiality checking.

Built for **Pick One Strategy** and **CoachStephen.AI** content publishing workflows.

## Features

- **Video Upload**: Direct upload or ingest from public URLs
- **AI Transcription**: Automatic captioning via n8n + AssemblyAI
- **AI Metadata**: Generate titles, descriptions, tags, hashtags
- **Confidentiality Check**: Scan for PII and sensitive information
- **YouTube Integration**: OAuth-based per-user publishing
- **Multi-user Support**: Each user connects their own YouTube channel

## Architecture

```
┌─────────────────┐     ┌─────────────────┐     ┌─────────────────┐
│   React SPA     │────▶│   FastAPI       │────▶│   PostgreSQL    │
│   (Frontend)    │     │   (Backend)     │     │   (Database)    │
└─────────────────┘     └────────┬────────┘     └─────────────────┘
                                 │
                    ┌────────────┴────────────┐
                    │                         │
              ┌─────▼─────┐           ┌───────▼───────┐
              │    n8n    │           │  OpenRouter   │
              │(Transcribe)│           │  (AI/LLM)    │
              └───────────┘           └───────────────┘
```

## Quick Start

### Prerequisites

- Docker & Docker Compose
- Traefik (for SSL/routing) or run locally
- n8n instance with transcription workflow
- OpenRouter API key
- YouTube OAuth credentials

### 1. Clone and Configure

```bash
# Copy environment template
cp .env.example .env

# Edit .env with your values
nano .env
```

### 2. Required Environment Variables

```env
# Database
POSTGRES_PASSWORD=your_secure_password

# Public URL (for n8n to reach videos)
PUBLIC_BASE_URL=https://video-studio.youromain.com

# n8n Webhooks
N8N_TRANSCRIBE_URL=https://your-n8n.com/webhook/transcribe
N8N_PUBLISH_URL=https://your-n8n.com/webhook/publish

# OpenRouter AI
OPENROUTER_API_KEY=sk-or-v1-xxxxxx

# YouTube OAuth (from Google Cloud Console)
YOUTUBE_CLIENT_ID=xxxxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxxxx
YOUTUBE_REDIRECT_URI=https://video-studio.yourdomain.com/oauth/youtube/callback
```

### 3. Deploy

```bash
# Create external network (if using Traefik)
docker network create traefik-network

# Start services
docker-compose up -d

# View logs
docker-compose logs -f
```

### 4. Access

- **Frontend**: https://video-studio.yourdomain.com
- **API Docs**: https://video-studio.yourdomain.com/api/docs
- **Health Check**: https://video-studio.yourdomain.com/api/health

## API Endpoints

### Videos

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /video | List all videos |
| GET | /video/{id} | Get video by ID |
| POST | /video/upload | Upload video file |
| POST | /video/ingest | Create from URL |
| PATCH | /video/{id} | Update video |
| DELETE | /video/{id} | Delete video |
| POST | /video/caption | Request AI transcription |
| POST | /video/metadata/generate | Generate AI metadata |
| POST | /video/confidentiality/check | Run confidentiality check |

### YouTube

| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /youtube/status | Check connection status |
| POST | /youtube/auth/start | Start OAuth flow |
| POST | /youtube/auth/callback | Exchange OAuth code |
| POST | /youtube/publish | Publish to YouTube |
| DELETE | /youtube/disconnect | Disconnect account |

## n8n Workflow Setup

### Transcription Webhook

Your n8n workflow should:

1. Receive POST to `/webhook/transcribe`
2. Accept `video_url` and `language_code` (form-encoded)
3. Download and transcribe the video (AssemblyAI, Whisper, etc.)
4. Return JSON: `{"text": "...", "srt": "..."}`

### Publish Webhook

Your n8n workflow should:

1. Receive POST to `/webhook/publish`
2. Accept JSON payload with video details
3. Upload to YouTube via YouTube Data API
4. Return JSON: `{"youtube_id": "...", "youtube_url": "..."}`

## YouTube OAuth Setup

1. Go to [Google Cloud Console](https://console.cloud.google.com)
2. Create a new project or select existing
3. Enable YouTube Data API v3
4. Create OAuth 2.0 credentials (Web application)
5. Add authorized redirect URI: `https://video-studio.yourdomain.com/oauth/youtube/callback`
6. Copy Client ID and Client Secret to `.env`

## Development

### Run Locally

```bash
# Backend
cd backend
pip install -r requirements.txt
uvicorn app.main:app --reload --port 8080

# Frontend
cd frontend
npm install
npm run dev
```

### Database Migrations

```bash
cd backend
alembic upgrade head
```

## Project Structure

```
video-studio/
├── backend/
│   ├── app/
│   │   ├── main.py          # FastAPI app
│   │   ├── config.py        # Settings
│   │   ├── db.py            # Database
│   │   ├── models.py        # SQLAlchemy models
│   │   ├── security.py      # Auth helpers
│   │   ├── api_videos.py    # Video endpoints
│   │   ├── api_youtube.py   # YouTube endpoints
│   │   └── services/        # Business logic
│   │       ├── n8n.py
│   │       ├── openrouter.py
│   │       ├── metadata.py
│   │       ├── confidentiality.py
│   │       └── youtube.py
│   ├── init.sql             # Database schema
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/
│   ├── src/
│   │   ├── main.tsx
│   │   ├── App.tsx
│   │   ├── types.ts
│   │   ├── api/
│   │   ├── components/
│   │   ├── pages/
│   │   └── styles/
│   ├── package.json
│   └── Dockerfile
├── docker-compose.yml
├── .env.example
└── README.md
```

## Integration with Pick One Strategy

This platform supports the Pick One Strategy workflow:

1. **Core Value Videos**: Business coaching content
2. **RED Method Tutorials**: Revise, Expand, Disrupt framework
3. **Client Testimonials**: Success story videos
4. **Educational Content**: Strategy implementation guides

The AI metadata generator is tuned to create engaging titles and descriptions optimized for business owners in the construction industry ($5-15M revenue).

## Support

For issues or questions:
- Check the API docs at `/api/docs`
- Review container logs: `docker-compose logs -f`
- Verify n8n webhook connectivity

---

Built with ❤️ for AskStephen.AI
