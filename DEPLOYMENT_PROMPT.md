# Video Studio - Deployment Prompt for Claude Code on Hostinger Linux VPS

Use this prompt with Claude Code on your Hostinger Linux VPS to deploy Video Studio
alongside your existing Docker stack (Traefik, PostgreSQL, n8n, Portainer).

---

## Quick Deployment Prompt

```
Deploy Video Studio from https://github.com/vanfwilson/Video-Studio
(branch: claude/video-publishing-spa-NWGra) to /opt/video-studio

My existing infrastructure:
- Traefik reverse proxy (network: traefik-network)
- PostgreSQL container (create new database for this app)
- n8n for automation workflows
- Portainer for management
- Cloudflare for DNS/SSL

Configuration needed:
- Domain: video-studio.askstephen.ai
- Use my existing PostgreSQL (create database: video_studio)
- OpenRouter API key for AI (use free models)
- YouTube OAuth credentials
- n8n webhook URLs for transcription and publishing

Deploy without spinning up a new PostgreSQL container - use existing one.
```

---

## Detailed Deployment Steps

### 1. Clone Repository

```bash
cd /opt
git clone https://github.com/vanfwilson/Video-Studio.git video-studio
cd video-studio
git checkout claude/video-publishing-spa-NWGra
```

### 2. Database Setup (Using Existing PostgreSQL)

Connect to your existing PostgreSQL container and create the database:

```bash
# Connect to your PostgreSQL container
docker exec -it your-postgres-container psql -U postgres

# In psql:
CREATE DATABASE video_studio;
CREATE USER video_studio WITH PASSWORD 'your_secure_password';
GRANT ALL PRIVILEGES ON DATABASE video_studio TO video_studio;
\c video_studio
\i /path/to/backend/init.sql
\q
```

Or copy init.sql into the container:
```bash
docker cp backend/init.sql your-postgres-container:/tmp/
docker exec -it your-postgres-container psql -U video_studio -d video_studio -f /tmp/init.sql
```

### 3. Configure Environment

```bash
cp .env.example .env
nano .env
```

**Key settings for Hostinger setup:**

```env
# Domain
VIDEO_STUDIO_DOMAIN=video-studio.askstephen.ai
PUBLIC_BASE_URL=https://video-studio.askstephen.ai

# Database - point to your existing PostgreSQL
DATABASE_URL=postgresql://video_studio:your_password@your-postgres-container:5432/video_studio

# Traefik
TRAEFIK_NETWORK=traefik-network
TRAEFIK_CERT_RESOLVER=cloudflare

# n8n webhooks (your existing n8n)
N8N_TRANSCRIBE_URL=https://your-n8n-domain.com/webhook/transcribe
N8N_PUBLISH_URL=https://your-n8n-domain.com/webhook/publish

# OpenRouter (use free model)
OPENROUTER_API_KEY=sk-or-v1-xxxxx
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# YouTube OAuth
YOUTUBE_CLIENT_ID=xxxxx.apps.googleusercontent.com
YOUTUBE_CLIENT_SECRET=xxxxx
YOUTUBE_REDIRECT_URI=https://video-studio.askstephen.ai/oauth/youtube/callback
```

### 4. Deploy (Without Built-in PostgreSQL)

```bash
# Deploy only the API and web containers (not the db)
docker-compose up -d --build video-studio-api video-studio-web
```

### 5. Verify Deployment

```bash
# Check containers
docker-compose ps

# View logs
docker-compose logs -f

# Test health
curl https://video-studio.askstephen.ai/api/health

# Test webhook health
curl https://video-studio.askstephen.ai/api/webhook/health
```

---

## n8n Webhook Integration

Video Studio uses **async webhooks** for n8n to send results back. This is because
n8n workflows may take time (transcription, YouTube upload) and can't always
return results directly.

### Workflow Pattern

```
┌─────────────┐         ┌─────────────┐         ┌─────────────┐
│ Video Studio│ ──────▶ │     n8n     │ ──────▶ │ Video Studio│
│ POST /api/  │ trigger │  workflow   │ callback│ POST /api/  │
│ video/caption        │  processes  │         │ webhook/    │
│             │         │  video      │         │ caption-result
└─────────────┘         └─────────────┘         └─────────────┘
```

### n8n Transcription Workflow

Your n8n transcription workflow should:

1. **Receive trigger** from Video Studio:
   ```
   POST to your n8n: /webhook/transcribe
   Body: { "video_url": "...", "video_id": 123, "language_code": "en" }
   ```

2. **Process video** (download, transcribe via AssemblyAI/Whisper)

3. **Send results back** to Video Studio:
   ```
   POST https://video-studio.askstephen.ai/api/webhook/caption-result
   Body: {
     "video_id": 123,
     "status": "success",
     "transcript": "Full text transcript...",
     "captions_srt": "1\n00:00:00,000 --> 00:00:05,000\nHello world...",
     "ai_summary": "Optional AI-generated title",
     "ai_description": "Optional AI-generated description"
   }
   ```

### n8n HTTP Request Node for Callback

```
Method: POST
URL: https://video-studio.askstephen.ai/api/webhook/caption-result
Body Type: JSON
Body:
{
  "video_id": {{$node["Start"].json.video_id}},
  "status": "success",
  "transcript": {{$node["Transcribe"].json.text}},
  "captions_srt": {{$node["Transcribe"].json.srt}}
}
```

### n8n Publish Workflow

Your n8n YouTube publish workflow should:

1. **Receive trigger** from Video Studio:
   ```
   POST to your n8n: /webhook/publish
   Body: { "video_id": 123, "video_url": "...", "title": "...", "description": "...", ... }
   ```

2. **Upload to YouTube** using YouTube Data API (your existing OAuth setup)

3. **Send results back** to Video Studio:
   ```
   POST https://video-studio.askstephen.ai/api/webhook/publish-result
   Body: {
     "video_id": 123,
     "status": "success",
     "youtube_id": "dQw4w9WgXcQ",
     "youtube_url": "https://youtube.com/watch?v=dQw4w9WgXcQ"
   }
   ```

### Webhook Endpoints Reference

| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/webhook/caption-result | n8n sends transcription results |
| POST | /api/webhook/publish-result | n8n sends YouTube publish results |
| POST | /api/webhook/update | Generic update endpoint |
| GET | /api/webhook/health | Webhook health check |

### Error Handling

If processing fails, n8n should send:
```json
{
  "video_id": 123,
  "status": "error",
  "error_message": "Description of what went wrong"
}
```

---

## API Endpoints Summary

### Video Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/health | Health check |
| GET | /api/video | List videos |
| GET | /api/video/{id} | Get video |
| POST | /api/video/upload | Upload video |
| POST | /api/video/ingest | Ingest from URL |
| PATCH | /api/video/{id} | Update video |
| DELETE | /api/video/{id} | Delete video |
| POST | /api/video/caption | Trigger transcription (calls n8n) |
| POST | /api/video/metadata/generate | Generate AI metadata |
| POST | /api/video/confidentiality/check | Check for PII |

### YouTube Operations
| Method | Endpoint | Description |
|--------|----------|-------------|
| GET | /api/youtube/status | Connection status |
| POST | /api/youtube/auth/start | Start OAuth flow |
| POST | /api/youtube/auth/callback | OAuth callback |
| POST | /api/youtube/publish | Trigger publish (calls n8n) |
| DELETE | /api/youtube/disconnect | Disconnect account |

### Webhook Callbacks (for n8n)
| Method | Endpoint | Description |
|--------|----------|-------------|
| POST | /api/webhook/caption-result | Receive transcription results |
| POST | /api/webhook/publish-result | Receive publish results |
| POST | /api/webhook/update | Generic update |
| GET | /api/webhook/health | Health check |

---

## Free OpenRouter Models

To minimize costs, use free models in `.env`:

```env
# Best free option (fast, good quality)
OPENROUTER_MODEL=google/gemini-2.0-flash-exp:free

# Alternatives:
# OPENROUTER_MODEL=google/gemini-exp-1206:free
# OPENROUTER_MODEL=meta-llama/llama-3.2-3b-instruct:free
```

---

## Portainer Stack Import

To import in Portainer:

1. Go to Stacks → Add Stack
2. Choose "Git Repository"
3. Repository URL: `https://github.com/vanfwilson/Video-Studio`
4. Branch: `claude/video-publishing-spa-NWGra`
5. Compose path: `docker-compose.yml`
6. Add environment variables from your `.env`
7. Deploy

---

## Troubleshooting

### Container won't start
```bash
docker-compose logs video-studio-api
docker-compose logs video-studio-web
```

### Database connection issues
- Verify DATABASE_URL points to correct PostgreSQL host
- Ensure video_studio database exists
- Check PostgreSQL container is on same network

### n8n callbacks not working
- Test webhook endpoint: `curl -X POST https://video-studio.askstephen.ai/api/webhook/health`
- Check n8n HTTP Request node URL is correct
- Verify video_id in payload matches existing video

### Traefik routing issues
- Verify traefik-network exists and is external
- Check Traefik dashboard for routing rules
- Ensure TRAEFIK_CERT_RESOLVER matches your setup

---

## Quick Commands

```bash
# Deploy
docker-compose up -d --build video-studio-api video-studio-web

# Logs
docker-compose logs -f video-studio-api

# Restart
docker-compose restart

# Update from GitHub
git pull origin claude/video-publishing-spa-NWGra
docker-compose up -d --build video-studio-api video-studio-web

# Shell into container
docker-compose exec video-studio-api bash
```
