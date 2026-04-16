from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import os

app = FastAPI()

# ✅ CORS FIX (THIS SOLVES "Failed to fetch")
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Folder to store videos
DOWNLOAD_FOLDER = "downloads"
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# ✅ TEST ROUTE
@app.get("/")
def home():
    return {"message": "API is running"}


# ✅ CREATE VIDEO (SIMULATED)
@app.get("/create/{filename}")
def create_file(filename: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.mp4")

    # Create a fake test video file
    with open(file_path, "w") as f:
        f.write("This is a test video file")

    return {"message": f"{filename}.mp4 created successfully"}


# ✅ DOWNLOAD VIDEO
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.mp4")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        path=file_path,
        media_type='application/octet-stream',
        filename=f"{filename}.mp4"
    )
