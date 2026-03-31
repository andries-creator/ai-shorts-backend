from fastapi import FastAPI, UploadFile, File
from fastapi.responses import JSONResponse
import shutil
import os
import uuid

app = FastAPI()

UPLOAD_FOLDER = "uploads"
OUTPUT_FOLDER = "outputs"

os.makedirs(UPLOAD_FOLDER, exist_ok=True)
os.makedirs(OUTPUT_FOLDER, exist_ok=True)

# Store jobs in memory (simple version)
jobs = {}

@app.get("/")
def home():
    return {"message": "Backend is running 🚀"}

# 1️⃣ Upload video
@app.post("/upload")
async def upload_video(file: UploadFile = File(...)):
    job_id = str(uuid.uuid4())

    input_path = f"{UPLOAD_FOLDER}/{job_id}_{file.filename}"
    output_path = f"{OUTPUT_FOLDER}/{job_id}_short.mp4"

    # Save uploaded file
    with open(input_path, "wb") as buffer:
        shutil.copyfileobj(file.file, buffer)

    # Save job info
    jobs[job_id] = {
        "status": "processing",
        "input": input_path,
        "output": output_path
    }

    # 👉 FAKE processing (for now just copy file)
    shutil.copy(input_path, output_path)

    jobs[job_id]["status"] = "done"

    return {"job_id": job_id}

# 2️⃣ Check status
@app.get("/status/{job_id}")
def check_status(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return {"error": "job not found"}

    return {"status": job["status"]}

# 3️⃣ Download result
@app.get("/download/{job_id}")
def download_video(job_id: str):
    job = jobs.get(job_id)

    if not job:
        return {"error": "job not found"}

    if job["status"] != "done":
        return {"error": "not ready"}

    return {"download_url": job["output"]}
