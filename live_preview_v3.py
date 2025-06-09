from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from picamera2 import Picamera2
import cv2
import threading
import time
import json
import os
import sys
import subprocess

app = FastAPI()

SETTINGS_FILE = "settings.json"

# Load persisted settings or use defaults
def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return tuple(data["resolution"]), data["framerate"]
    return (640, 480), 20

# Save settings to disk
def save_settings(resolution, framerate):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "resolution": list(resolution),
            "framerate": framerate
        }, f)

# Global state
current_resolution, current_framerate = load_settings()
frame_lock = threading.Lock()
frame = None

# Initialize camera
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": current_resolution, "format": "RGB888"})
picam2.configure(config)
picam2.start()

def capture_frames():
    global frame
    while True:
        new_frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', new_frame)
        with frame_lock:
            frame = jpeg.tobytes()
        time.sleep(1 / current_framerate)

threading.Thread(target=capture_frames, daemon=True).start()

def mjpeg_stream():
    while True:
        with frame_lock:
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
        time.sleep(1 / current_framerate)

@app.get("/", response_class=HTMLResponse)
def index():
    return f"""
    <html>
        <head><title>PiCam Stream</title></head>
        <body>
            <h2>Live Preview</h2>
            <img src="/video" width="{current_resolution[0]}" height="{current_resolution[1]}" />
            <h3>Settings</h3>
            <form method="post" action="/set">
                <label>Resolution:</label>
                <select name="resolution">
                    <option value="640x480" {"selected" if current_resolution == (640, 480) else ""}>640x480</option>
                    <option value="320x240" {"selected" if current_resolution == (320, 240) else ""}>320x240</option>
                    <option value="1280x720" {"selected" if current_resolution == (1280, 720) else ""}>1280x720</option>
                </select>
                <label>Framerate:</label>
                <select name="framerate">
                    <option value="5" {"selected" if current_framerate == 5 else ""}>5 FPS</option>
                    <option value="10" {"selected" if current_framerate == 10 else ""}>10 FPS</option>
                    <option value="20" {"selected" if current_framerate == 20 else ""}>20 FPS</option>
                    <option value="30" {"selected" if current_framerate == 30 else ""}>30 FPS</option>
                </select>
                <input type="submit" value="Apply and Restart" />
            </form>
        </body>
    </html>
    """

@app.post("/set")
def set_params(resolution: str = Form(...), framerate: int = Form(...)):
    width, height = map(int, resolution.split('x'))
    new_resolution = (width, height)
    new_framerate = framerate

    save_settings(new_resolution, new_framerate)

    print(f"[INFO] Settings saved: {new_resolution}, {new_framerate} FPS")
    print("[INFO] Restarting server...")

    # Schedule a delayed restart using subprocess (non-blocking)
    subprocess.Popen(["/usr/bin/python3", sys.argv[0]])
    os._exit(0)  # Force current process to exit

    return RedirectResponse("/", status_code=303)

@app.get("/video")
def video():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
