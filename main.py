import os, uuid, asyncio, json, glob, subprocess, shutil
from pathlib import Path
from fastapi import FastAPI, UploadFile, File, Form, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse, StreamingResponse
from typing import Optional
import zipfile, io

app = FastAPI(title="AI Gaming Shorts Generator")
app.add_middleware(CORSMiddleware, allow_origins=["*"], allow_methods=["*"], allow_headers=["*"])

UPLOAD_DIR = Path(os.getenv("UPLOAD_DIR", "./uploads"))
OUTPUT_DIR = Path(os.getenv("OUTPUT_DIR", "./outputs"))
UPLOAD_DIR.mkdir(parents=True, exist_ok=True)
OUTPUT_DIR.mkdir(parents=True, exist_ok=True)

jobs: dict = {}

# ── helpers ──────────────────────────────────────────────

def get_duration(path: str) -> float:
    r = subprocess.run(
        ["ffprobe", "-v", "error", "-show_entries", "format=duration",
         "-of", "default=noprint_wrappers=1:nokey=1", path],
        capture_output=True, text=True,
    )
    return float(r.stdout.strip())

def detect_highlights(path: str, clip_min: int, clip_max: int, max_clips: int) -> list[dict]:
    """Simple heuristic: split video into equal segments, pick loudest ones via volume detection."""
    duration = get_duration(path)
    segment_len = max(clip_min, min(clip_max, duration // (max_clips + 2)))
    segments = []
    t = 5.0  # skip first 5s intro
    while t + segment_len <= duration - 2 and len(segments) < max_clips * 3:
        # measure mean volume of segment
        r = subprocess.run(
            ["ffmpeg", "-ss", str(t), "-t", str(segment_len), "-i", path,
             "-af", "volumedetect", "-f", "null", "-"],
            capture_output=True, text=True,
        )
        mean_vol = -50.0
        for line in r.stderr.splitlines():
            if "mean_volume" in line:
                try:
                    mean_vol = float(line.split("mean_volume:")[1].strip().split()[0])
                except Exception:
                    pass
        segments.append({"start": t, "duration": segment_len, "volume": mean_vol})
        t += segment_len * 0.5  # overlap
    # pick top N by volume (loudest = most action)
    segments.sort(key=lambda s: s["volume"], reverse=True)
    # remove overlapping
    chosen = []
    for seg in segments:
        if len(chosen) >= max_clips:
            break
        overlap = any(abs(seg["start"] - c["start"]) < segment_len * 0.6 for c in chosen)
        if not overlap:
            chosen.append(seg)
    chosen.sort(key=lambda s: s["start"])
    return chosen

def extract_clip(source: str, start: float, duration: float, out_path: str):
    """Extract and convert to vertical 9:16 with padding."""
    subprocess.run([
        "ffmpeg", "-y", "-ss", str(start), "-t", str(duration), "-i", source,
        "-vf", "scale=1080:1920:force_original_aspect_ratio=decrease,pad=1080:1920:(ow-iw)/2:(oh-ih)/2:black",
        "-c:v", "libx264", "-preset", "fast", "-crf", "23",
        "-c:a", "aac", "-b:a", "128k",
        out_path,
    ], check=True, capture_output=True)

def generate_thumbnail(video_path: str, thumb_path: str):
    subprocess.run([
        "ffmpeg", "-y", "-i", video_path, "-ss", "1", "-vframes", "1",
        "-vf", "scale=540:960", thumb_path,
    ], capture_output=True)

def transcribe_clip(video_path: str) -> str:
    """Use Whisper to transcribe audio. Falls back gracefully."""
    try:
        import whisper
        model = whisper.load_model("base")
        result = model.transcribe(video_path, language="en", fp16=False)
        return result.get("text", "").strip()
    except ImportError:
        return "(Whisper not installed — install openai-whisper)"
    except Exception as e:
        return f"(transcription failed: {e})"

HOOK_TEXTS = [
    "THIS WAS INSANE 😱", "WAIT FOR IT…", "NO WAY THIS HAPPENED 🤯",
    "I CAN'T BELIEVE THIS 😭", "PURE CHAOS 🔥", "CLUTCH MOMENT 💀",
    "HOW DID I SURVIVE?!", "BEST PLAY EVER 🏆",
]

# ── background processing ────────────────────────────────

async def process_job(job_id: str):
    job = jobs[job_id]
    try:
        job["status"] = "processing"
        job["step"] = 1
        job["progress"] = 10

        src = str(job["source_path"])
        clip_min = job.get("clip_length_min", 15)
        clip_max = job.get("clip_length_max", 30)
        max_clips = job.get("max_clips", 6)
        game_title = job.get("game_title", "Unknown Game")
        job_dir = OUTPUT_DIR / job_id
        job_dir.mkdir(parents=True, exist_ok=True)

        # Step 2: detect highlights
        job["step"] = 2; job["progress"] = 25
        highlights = await asyncio.to_thread(detect_highlights, src, clip_min, clip_max, max_clips)

        clips = []
        total = len(highlights)
        for i, hl in enumerate(highlights):
            # Step 3: extract clips
            job["step"] = 3
            job["progress"] = 30 + int(50 * (i / total))

            clip_id = str(uuid.uuid4())
            clip_path = str(job_dir / f"{clip_id}.mp4")
            thumb_path = str(job_dir / f"{clip_id}.jpg")

            await asyncio.to_thread(extract_clip, src, hl["start"], hl["duration"], clip_path)
            await asyncio.to_thread(generate_thumbnail, clip_path, thumb_path)

            # Step 4: transcribe
            job["step"] = 4
            caption = await asyncio.to_thread(transcribe_clip, clip_path)
            hook = HOOK_TEXTS[i % len(HOOK_TEXTS)]

            clips.append({
                "id": clip_id,
                "title": f"This {game_title} moment is pure chaos 🔥" if i == 0 else f"{game_title} clip #{i+1}",
                "hook_text": hook,
                "duration": round(hl["duration"]),
                "thumbnail_url": f"/download/{clip_id}.jpg",
                "video_url": f"/download/{clip_id}.mp4",
                "score": max(50, min(99, 70 + int(hl["volume"] + 50))),
                "caption": caption,
            })

        job["clips"] = clips
        job["status"] = "done"
        job["progress"] = 100
        job["step"] = 4

        # create zip
        zip_path = str(job_dir / "all_clips.zip")
        with zipfile.ZipFile(zip_path, "w") as zf:
            for c in clips:
                mp4 = str(job_dir / f"{c['id']}.mp4")
                zf.write(mp4, f"{c['title']}.mp4")
        job["zip_path"] = zip_path

    except Exception as e:
        job["status"] = "error"
        job["error"] = str(e)
    finally:
        # cleanup source
        try:
            os.remove(job["source_path"])
        except Exception:
            pass

# ── routes ───────────────────────────────────────────────

@app.post("/upload")
async def upload(
    video: UploadFile = File(...),
    game_title: str = Form("Unknown Game"),
    clip_length_min: int = Form(15),
    clip_length_max: int = Form(30),
    max_clips: int = Form(6),
):
    job_id = str(uuid.uuid4())
    ext = Path(video.filename or "video.mp4").suffix
    dest = UPLOAD_DIR / f"{job_id}{ext}"
    with open(dest, "wb") as f:
        while chunk := await video.read(1024 * 1024):
            f.write(chunk)

    jobs[job_id] = {
        "status": "queued", "progress": 0, "step": 0,
        "source_path": str(dest), "game_title": game_title,
        "clip_length_min": clip_length_min, "clip_length_max": clip_length_max,
        "max_clips": max_clips, "clips": [], "error": None,
    }
    asyncio.create_task(process_job(job_id))
    return {"job_id": job_id}

@app.get("/status/{job_id}")
async def status(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    j = jobs[job_id]
    return {"job_id": job_id, "status": j["status"], "progress": j["progress"],
            "step": j["step"], "error": j.get("error")}

@app.get("/results/{job_id}")
async def results(job_id: str):
    if job_id not in jobs:
        raise HTTPException(404, "Job not found")
    j = jobs[job_id]
    if j["status"] != "done":
        raise HTTPException(400, "Job not done yet")
    return {"job_id": job_id, "clips": j["clips"],
            "zip_url": f"/download/{job_id}/zip" if j.get("zip_path") else None}

@app.get("/download/{clip_id}.{ext}")
async def download_file(clip_id: str, ext: str):
    for jid, j in jobs.items():
        p = OUTPUT_DIR / jid / f"{clip_id}.{ext}"
        if p.exists():
            mt = "video/mp4" if ext == "mp4" else "image/jpeg"
            return FileResponse(p, media_type=mt, filename=f"{clip_id}.{ext}")
    raise HTTPException(404, "File not found")

@app.get("/download/{job_id}/zip")
async def download_zip(job_id: str):
    if job_id not in jobs or not jobs[job_id].get("zip_path"):
        raise HTTPException(404, "Zip not found")
    return FileResponse(jobs[job_id]["zip_path"], media_type="application/zip",
                        filename="gaming_shorts.zip")
