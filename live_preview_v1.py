from fastapi import FastAPI, Response
from fastapi.responses import StreamingResponse
from picamera2 import Picamera2
import cv2
import threading
import time
import io

app = FastAPI()
picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration(main={"size": (640, 480)}))
picam2.start()

frame_lock = threading.Lock()
frame = None

def capture_frames():
    global frame
    while True:
        new_frame = picam2.capture_array()
        _, jpeg = cv2.imencode('.jpg', new_frame)
        with frame_lock:
            frame = jpeg.tobytes()
        time.sleep(0.05)  # ~20 FPS

threading.Thread(target=capture_frames, daemon=True).start()

def mjpeg_stream():
    while True:
        with frame_lock:
            if frame:
                yield (b"--frame\r\n"
                       b"Content-Type: image/jpeg\r\n\r\n" + frame + b"\r\n")
        time.sleep(0.05)

@app.get("/")
def root():
    return Response(content="<img src='/video' />", media_type="text/html")

@app.get("/video")
def video():
    return StreamingResponse(mjpeg_stream(), media_type="multipart/x-mixed-replace; boundary=frame")
