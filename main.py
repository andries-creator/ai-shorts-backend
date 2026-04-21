from fastapi import FastAPI, UploadFile, File, Form
from fastapi.responses import FileResponse, JSONResponse
from fastapi.middleware.cors import CORSMiddleware
import uuid
import os
import shutil
import subprocess

app = FastAPI()

# ✅ CORS (fixes frontend issues)
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

jobs = {}

# -----------------------------
# CREATE CLIPS (FIXED + STABLE)
# -----------------------------
def create_clips(input_path, job_id):
    output_paths = []

    job_folder = os.path.join(OUTPUT_FOLDER, job_id)
    os.makedirs(job_folder, exist_ok=True)

    timestamps = [5, 15, 30]

    for i, start in enumerate(timestamps):
        output_file = os.path.join(job_folder, f"clip_{i}.mp4")

        command = [
            "ffmpeg",
            "-y",

            # safer input handling
            "-i", input_path,
            "-ss", str(start),

            "-t", "15",

            # force vertical + compatibility
            "-vf", "scale=720:1280:force_original_aspect_ratio=decrease,"
                   "pad=720:1280:(ow-iw)/2:(oh-ih)/2,format=yuv420p",

            # video encoding
            "-c:v", "libx264",
            "-profile:v", "baseline",
            "-level", "3.0",
            "-pix_fmt", "yuv420p",
            "-preset", "veryfast",
            "-crf", "28",

            # audio encoding
            "-c:a", "aac",
            "-b:a", "128k",
            "-ar", "44100",
            "-ac", "2",

            # better playback
            "-movflags", "+faststart",

            output_file
        ]

        result = subprocess.run(command, capture_output=True, text=True)

        if result.returncode != 0:
            print("FFMPEG ERROR:", result.stderr)
            raise Exception(result.stderr)

        # verify file exists
        if not os.path.exists(output_file):
            raise Exception("Clip not created")

        size = os.path.getsize(output_file)
        print(f"Clip {i} size:", size)

        if size < 100000:  # 100KB safety check
            raise Exception("Clip too small → likely corrupted")

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

    # save uploaded file
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
# CHECK RESULTS
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
        return FileResponse(
            file_path,
            media_type="video/mp4",
            filename=os.path.basename(file_path)
        )
    except:
        return {"error": "file not found"}
