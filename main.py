from fastapi import FastAPI, HTTPException
from fastapi.responses import FileResponse
import os

app = FastAPI()

# Folder where videos are stored
DOWNLOAD_FOLDER = "downloads"

# Ensure folder exists
os.makedirs(DOWNLOAD_FOLDER, exist_ok=True)


# TEST ROUTE (to confirm API works)
@app.get("/")
def home():
    return {"message": "API is running"}


# SAVE / SIMULATE VIDEO (TEST)
@app.get("/create/{filename}")
def create_file(filename: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.mp4")

    # Create a fake test file
    with open(file_path, "w") as f:
        f.write("This is a test video file")

    return {"message": f"{filename}.mp4 created successfully"}


# DOWNLOAD ROUTE (THIS WAS MISSING OR WRONG)
@app.get("/download/{filename}")
def download_file(filename: str):
    file_path = os.path.join(DOWNLOAD_FOLDER, f"{filename}.mp4")

    if not os.path.exists(file_path):
        raise HTTPException(status_code=404, detail="File not found")

    return FileResponse(
        file_path,
        media_type='application/octet-stream',
        filename=f"{filename}.mp4"
    )
