from fastapi import FastAPI, BackgroundTasks
from fastapi.responses import FileResponse
import os
import subprocess

app = FastAPI()

# Create output folder
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)

# Job storage
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

    background_tasks.add_task(create_video, job_id)

    return {
        "job_id": job_id,
        "status": "processing"
    }


# 🔥 REAL CLIP CREATION FROM VIDEO
def create_video(job_id: str):
    input_file = "input.mp4"  # must exist
    output_file = os.path.join(OUTPUT_DIR, f"{job_id}.mp4")

    # Cut 20 seconds starting at 1 minute
    command = [
        "ffmpeg",
        "-i", input_file,
        "-ss", "00:01:00",
        "-t", "20",
        "-vf", "scale=1080:1920",
        "-y",
        output_file
    ]

    subprocess.run(command)

    jobs[job_id]["status"] = "done"
    jobs[job_id]["file"] = output_file


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
