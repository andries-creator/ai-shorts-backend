from fastapi import FastAPI, UploadFile, File
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os
import shutil
import subprocess
import uuid

app = FastAPI()

# CORS
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


@app.get("/")
def home():
    return {"message": "API running"}


# ✅ UPLOAD + PROCESS VIDEO
@app.post("/upload")
def upload_video(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    input_path = os.path.join(UPLOAD_FOLDER, f"{job_id}.mp4")
    output_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.mp4")

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # 🎬 Create SHORT (basic clip for now)
    subprocess.run([
        "ffmpeg",
        "-i", input_path,
        "-ss", "00:00:10",
        "-t", "15",
        "-vf", "scale=1080:1920",
        "-y",
        output_path
    ])

    return {
        "message": "Video processed",
        "job_id": job_id
    }


# ✅ DOWNLOAD RESULT
@app.get("/download/{job_id}")
def download_video(job_id: str):
    file_path = os.path.join(OUTPUT_FOLDER, f"{job_id}.mp4")

    if not os.path.exists(file_path):
        return {"error": "File not found"}

    return FileResponse(file_path, media_type="video/mp4", filename=f"{job_id}.mp4")
