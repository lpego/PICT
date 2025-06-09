from fastapi import FastAPI, Form
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from picamera2 import Picamera2
from picamera2 import controls
import cv2
import threading
import time
import json
import os
import sys
import subprocess

app = FastAPI()

SETTINGS_FILE = "settings.json"

def load_settings():
    if os.path.exists(SETTINGS_FILE):
        with open(SETTINGS_FILE, "r") as f:
            data = json.load(f)
            return {
                "resolution": tuple(data["resolution"]),
                "framerate": data["framerate"],
                "autofocus": data.get("autofocus", True),
                "manual_focus": data.get("manual_focus", 512),
            }
    return {
        "resolution": (640, 480),
        "framerate": 20,
        "autofocus": True,
        "manual_focus": 512,
    }

def save_settings(settings):
    with open(SETTINGS_FILE, "w") as f:
        json.dump({
            "resolution": list(settings["resolution"]),
            "framerate": settings["framerate"],
            "autofocus": settings["autofocus"],
            "manual_focus": settings["manual_focus"]
        }, f)

settings = load_settings()

# Global state
frame_lock = threading.Lock()
frame = None

# Initialize camera
picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": settings["resolution"], "format": "RGB888"})
picam2.configure(config)
picam2.start()

# Apply focus controls
def apply_focus_controls():
    if settings["autofocus"]:
        picam2.set_controls({
            "AfMode": controls.AfModeEnum.Continuous
        })
    else:
        picam2.set_controls({
            "AfMode": controls.AfModeEnum.Manual,
            "LensPosition": float(settings["manual_focus"])
        })

apply_focus_controls()

def capture_frames():
    global frame
    while True:
        new_frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', new_frame)
        with frame_lock:
            frame = jpeg.tobytes()
        time.sleep(1 / settings["framerate"])

threading.Thread(target=capture_frames, daemon=True).start()

def mjpeg_stream():
    while True:
        with frame_lock:
            if frame:
                yield (
                    b"--frame\r\n"
                    b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n"
                )
        time.sleep(1 / settings["framerate"])

@app.get("/", response_class=HTMLResponse)
def index():
    autofocus_checked = "selected" if settings["autofocus"] else ""
    manual_checked = "" if settings["autofocus"] else "selected"
    return f"""
    <html>
        <head>
            <title>PiCam Stream</title>
            <script>
                function toggleFocusInput() {{
                    const af = document.getElementById("autofocus").value;
                    document.getElementById("manual-focus-input").style.display = (af === "off") ? "inline" : "none";
                }}
                window.onload = toggleFocusInput;
            </script>
        </head>
        <body>
            <h2>Live Preview</h2>
            <img src="/video" width="{settings['resolution'][0]}" height="{settings['resolution'][1]}" />
            <h3>Settings</h3>
            <form method="post" action="/set">
                <label>Resolution:</label>
                <select name="resolution">
                    <option value="640x480" {"selected" if settings["resolution"] == (640, 480) else ""}>640x480</option>
                    <option value="320x240" {"selected" if settings["resolution"] == (320, 240) else ""}>320x240</option>
                    <option value="1280x720" {"selected" if settings["resolution"] == (1280, 720) else ""}>1280x720</option>
                </select>

                <label>Framerate:</label>
                <select name="framerate">
                    <option value="5" {"selected" if settings["framerate"] == 5 else ""}>5 FPS</option>
                    <option value="10" {"selected" if settings["framerate"] == 10 else ""}>10 FPS</option>
                    <option value="20" {"selected" if settings["framerate"] == 20 else ""}>20 FPS</option>
                    <option value="30" {"selected" if settings["framerate"] == 30 else ""}>30 FPS</option>
                </select>

                <label>Autofocus:</label>
                <select name="autofocus" id="autofocus" onchange="toggleFocusInput()">
                    <option value="on" {autofocus_checked}>On</option>
                    <option value="off" {manual_checked}>Off</option>
                </select>

                <span id="manual-focus-input" style="display:none;">
                    <label>Manual Focus (0-1024):</label>
                    <input type="number" name="manual_focus" min="0" max="1024" value="{settings['manual_focus']}" />
                </span>

                <br><br>
                <input type="submit" value="Apply and Restart" />
            </form>
        </body>
    </html>
    """

@app.post("/set")
def set_params(
    resolution: str = Form(...),
    framerate: int = Form(...),
    autofocus: str = Form(...),
    manual_focus: int = Form(512)
):
    width, height = map(int, resolution.split('x'))
    new_settings = {
        "resolution": (width, height),
        "framerate": framerate,
        "autofocus": (autofocus == "on"),
        "manual_focus": manual_focus
    }

    save_settings(new_settings)
    print(f"[INFO] Settings saved: {new_settings}")
    print("[INFO] Restarting server...")

    # Restart script
    subprocess.Popen(["/usr/bin/python3", sys.argv[0]])
    os._exit(0)

@app.get("/video")
def video():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
