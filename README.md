# AI Gaming Shorts Generator — Backend

FastAPI backend that processes gameplay videos into short-form vertical clips.

## Features
- FFmpeg-based highlight detection (volume analysis)
- Automatic 9:16 vertical reformatting
- Whisper speech-to-text transcription
- ZIP download of all clips

## Quick Start

```bash
# Local
pip install -r requirements.txt
uvicorn main:app --reload

# Docker
docker build -t gaming-shorts-backend .
docker run -p 8000:8000 gaming-shorts-backend
```

## Deploy
Push to **Railway**, **Render**, or **Fly.io** — just point the repo
and it will auto-detect the Dockerfile.

Then set your frontend Settings → Backend URL to your deployed URL
(e.g. `https://your-app.railway.app`).

## API Endpoints
| Method | Path | Description |
|--------|------|-------------|
| POST | `/upload` | Upload video + config |
| GET | `/status/{job_id}` | Poll processing status |
| GET | `/results/{job_id}` | Get clip metadata |
| GET | `/download/{clip_id}.mp4` | Download clip |
| GET | `/download/{job_id}/zip` | Download all clips |
