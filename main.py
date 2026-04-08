from fastapi import FastAPI
from fastapi.responses import FileResponse
import os
import subprocess

app = FastAPI()

# ✅ Create outputs folder
OUTPUT_DIR = "outputs"
os.makedirs(OUTPUT_DIR, exist_ok=True)


# ✅ GENERATE VIDEO
@app.post("/generate")
def generate_video(data: dict):
    topic = data.get("topic", "test")

    # Clean filename
    filename = topic.replace(" ", "_") + ".mp4"
    filepath = os.path.join(OUTPUT_DIR, filename)

    # ✅ Create test video using FFmpeg
    subprocess.run([
        "ffmpeg",
        "-y",  # overwrite if exists
        "-f", "lavfi",
        "-i", "color=c=blue:s=720x1280:d=5",
        "-vf", f"drawtext=text='{topic}':fontcolor=white:fontsize=40:x=(w-text_w)/2:y=(h-text_h)/2",
        filepath
    ])

    # Debug log
    print("Saved video to:", filepath)
    print("Files in folder:", os.listdir(OUTPUT_DIR))

    return {
        "message": "Video created",
        "filename": filename
    }


# ✅ DOWNLOAD VIDEO
@app.get("/download/{video_name}")
def download_video(video_name: str):
    filepath = os.path.join(OUTPUT_DIR, f"{video_name}.mp4")

    if os.path.exists(filepath):
        return FileResponse(filepath, media_type="video/mp4", filename=video_name + ".mp4")
    else:
        return {"error": "File not found"}
