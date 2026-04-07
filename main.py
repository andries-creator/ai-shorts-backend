from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import JSONResponse
import uuid
import shutil
import os
import json

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"
JOBS_FILE = "jobs.json"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# 📦 LOAD JOBS FROM FILE
def load_jobs():
    if not os.path.exists(JOBS_FILE):
        return {}
    with open(JOBS_FILE, "r") as f:
        return json.load(f)

# 💾 SAVE JOBS TO FILE
def save_jobs(jobs):
    with open(JOBS_FILE, "w") as f:
        json.dump(jobs, f)

# Initialize jobs
jobs = load_jobs()


@app.get("/")
def home():
    return {"message": "Backend is running"}


# 🚀 UPLOAD VIDEO
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    game_title: str = Form(...),
    clip_length_min: int = Form(...),
    clip_length_max: int = Form(...),
    max_clips: int = Form(...)
):
    try:
        jobs = load_jobs()

        job_id = str(uuid.uuid4())
        file_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{file.filename}")

        # Save uploaded file
        with open(file_path, "wb") as buffer:
            shutil.copyfileobj(file.file, buffer)

        # Store job
        jobs[job_id] = {
            "status": "processing",
            "file_path": file_path,
            "clips": []
        }

        # 💾 SAVE immediately
        save_jobs(jobs)

        # 🔥 SIMULATED PROCESSING (for now)
        jobs[job_id]["status"] = "done"
        jobs[job_id]["clips"] = [
            f"/download/{job_id}_clip1.mp4",
            f"/download/{job_id}_clip2.mp4"
        ]

        # 💾 SAVE again after processing
        save_jobs(jobs)

        return {
            "job_id": job_id,
            "status": "processing"
        }

    except Exception as e:
        return JSONResponse(
            status_code=500,
            content={"error": str(e)}
        )


# 📊 CHECK STATUS
@app.get("/status/{job_id}")
def check_status(job_id: str):
    jobs = load_jobs()

    if job_id not in jobs:
        return {"error": "Job not found"}

    return {
        "job_id": job_id,
        "status": jobs[job_id]["status"]
    }


# 📦 GET RESULTS
@app.get("/results/{job_id}")
def get_results(job_id: str):
    jobs = load_jobs()

    if job_id not in jobs:
        return {"error": "Job not found"}

    return {
        "job_id": job_id,
        "clips": jobs[job_id]["clips"]
    }


# 🎬 DOWNLOAD (mock for now)
@app.get("/download/{clip_name}")
def download_clip(clip_name: str):
    return {
        "message": f"Download {clip_name} (not implemented yet)"
    }
