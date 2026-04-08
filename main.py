from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
import os
import subprocess
import time

app = FastAPI()

# Create output folder
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# In-memory job storage
jobs = {}


# 🔥 ROOT
@app.get("/")
def home():
    return {"message": "AI Shorts Backend Running 🚀"}


# 🔥 GENERATE VIDEO
@app.post("/generate/{topic}")
def generate_video(topic: str, background_tasks: BackgroundTasks):
    job_id = topic.replace(" ", "_")

    jobs[job_id] = {"status": "processing"}

    background_tasks.add_task(create_video, job_id, topic)

    return {
        "job_id": job_id,
        "status": "processing"
    }


# 🔥 BACKGROUND VIDEO CREATION (REAL FFmpeg)
def create_video(job_id: str, topic: str):
    file_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    text = f"{topic} - Viral Short"

    command = [
        "ffmpeg",
        "-f", "lavfi",
        "-i", "color=c=black:s=1080x1920:d=6",
        "-vf",
        f"drawtext=text='{text}':fontcolor=white:fontsize=60:x=(w-text_w)/2:y=(h-text_h)/2",
        "-y",
        file_path
    ]

    subprocess.run(command)

    # Mark job done
    jobs[job_id]["status"] = "done"
    jobs[job_id]["file"] = file_path


# 🔥 CHECK STATUS
@app.get("/status/{job_id}")
def check_status(job_id: str):
    if job_id not in jobs:
        return {"error": "Job not found"}

    return jobs[job_id]


# 🔥 DOWNLOAD VIDEO
@app.get("/download/{job_id}")
def download(job_id: str):
    file_path = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(
        path=file_path,
        media_type="video/mp4",
        filename=f"{job_id}.mp4"
    )
