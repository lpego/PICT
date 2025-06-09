from fastapi import FastAPI, Request, Response, Form
from fastapi.responses import StreamingResponse, HTMLResponse, RedirectResponse
from picamera2 import Picamera2
import cv2
import threading
import time

app = FastAPI()

picam2 = Picamera2()
config = picam2.create_video_configuration(main={"size": (640, 480), "format": "RGB888"})
picam2.configure(config)
picam2.start()

frame_lock = threading.Lock()
frame = None
resolution = (640, 480)
framerate = 20

def capture_frames():
    global frame
    while True:
        new_frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', new_frame)
        with frame_lock:
            frame = jpeg.tobytes()
        time.sleep(1 / framerate)

threading.Thread(target=capture_frames, daemon=True).start()

def mjpeg_stream():
    while True:
        with frame_lock:
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(1 / framerate)

@app.get("/", response_class=HTMLResponse)
def index():
    return """
    <html>
        <head><title>PiCam Stream</title></head>
        <body>
            <h2>Live Preview</h2>
            <img src="/video" width="640" height="480" />
            <h3>Settings</h3>
            <form method="post" action="/set">
                <label>Resolution:</label>
                <select name="resolution">
                    <option value="640x480">640x480</option>
                    <option value="320x240">320x240</option>
                    <option value="1280x720">1280x720</option>
                </select>
                <label>Framerate:</label>
                <select name="framerate">
                    <option value="5">5 FPS</option>
                    <option value="10">10 FPS</option>
                    <option value="20" selected>20 FPS</option>
                    <option value="30">30 FPS</option>
                </select>
                <input type="submit" value="Apply" />
            </form>
        </body>
    </html>
    """

@app.post("/set")
def set_params(resolution_str: str = Form(...), framerate: int = Form(...)):
    global resolution, framerate, picam2

    width, height = map(int, resolution_str.split('x'))
    resolution = (width, height)

    # Stop, reconfigure, and restart the camera
    picam2.stop()
    config = picam2.create_video_configuration(main={"size": resolution, "format": "RGB888"})
    picam2.configure(config)
    picam2.start()

    return RedirectResponse("/", status_code=303)

@app.get("/video")
def video():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
