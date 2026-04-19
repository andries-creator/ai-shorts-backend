from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
import uuid
import os
import shutil
import subprocess

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

# -----------------------------
# CREATE CLIPS FUNCTION (FIXED)
# -----------------------------
def create_clips(input_path, job_id):
    output_paths = []

    job_folder = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_folder, exist_ok=True)

    timestamps = [10, 30, 50]

    for i, start in enumerate(timestamps):
        output_file = os.path.join(job_folder, f"clip_{i}.mp4")

        # ✅ FIXED FFMPEG COMMAND (NO MORE CORRUPT FILES)
        command = [
            "ffmpeg",
            "-y",
            "-ss", str(start),
            "-i", input_path,
            "-t", "20",
            "-vf", "scale=720:1280",
            "-c:v", "libx264",
            "-preset", "fast",
            "-crf", "23",
            "-c:a", "aac",
            "-b:a", "128k",
            output_file
        ]

        subprocess.run(command)

        output_paths.append(output_file)

    return output_paths


# -----------------------------
# UPLOAD ENDPOINT
# -----------------------------
@app.post("/upload")
async def upload_video(
    file: UploadFile = File(...),
    game_title: str = Form(...),
    clip_length_min: int = Form(...),
    clip_length_max: int = Form(...)
):
    job_id = str(uuid.uuid4())
    file_path = os.path.join(UPLOAD_FOLDER, f"{job_id}_{file.filename}")

    with open(file_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    jobs[job_id] = {
        "status": "processing",
        "files": []
    }

    try:
        clips = create_clips(file_path, job_id)

        jobs[job_id]["status"] = "completed"
        jobs[job_id]["files"] = clips

    except Exception as e:
        jobs[job_id]["status"] = "error"
        jobs[job_id]["error"] = str(e)

    return {"job_id": job_id}


# -----------------------------
# GET RESULTS
# -----------------------------
@app.get("/results/{job_id}")
def get_results(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return {"error": "job not found"}

    return job


# -----------------------------
# DOWNLOAD CLIP
# -----------------------------
@app.get("/download/{job_id}/{clip_index}")
def download_clip(job_id: str, clip_index: int):
    job = jobs.get(job_id)

    if not job or job["status"] != "completed":
        return JSONResponse(content={"error": "job not ready"}, status_code=400)

    try:
        file_path = job["files"][clip_index]
        return FileResponse(file_path, media_type="video/mp4", filename=os.path.basename(file_path))
    except:
        return {"error": "file not found"}
