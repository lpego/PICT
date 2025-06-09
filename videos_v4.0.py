import socket
import uuid
from datetime import datetime as dt
import time
import cv2
import os 
from picamera2 import Picamera2
from libcamera import controls
import signal
import sys

## Signal handling for graceful shutdown
running = True

def signal_handler(sig, frame):
    global running
    print(f"Received signal {sig}, shutting down...")
    running = False

# Register the signal handler
signal.signal(signal.SIGINT, signal_handler)  # For Ctrl+C
signal.signal(signal.SIGTERM, signal_handler) # For kill

video_duration = 1800 # each video's length in seconds
video_number = 336 # max number of videos to record
Framerate = 5  # Set the desired framerate here
Focus = "Auto"  # Set to "Auto" or "Manual"
Focus_distance = 30.0  # Only used if Focus is "Manual"; must be between 0 and 1024
UID = dt.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

picam2 = Picamera2()

if Focus == "Auto":
    controls_dict = {
        "FrameRate": Framerate,
        "AfMode": controls.AfModeEnum.Continuous
    }
elif Focus == "Manual":
    lens_position = Focus_distance if 0 <= Focus_distance <= 1024 else 30.0
    controls_dict = {
        "FrameRate": Framerate,
        "AfMode": controls.AfModeEnum.Manual,
        "LensPosition": lens_position
    }
else:
    raise ValueError("Focus must be either 'Auto' or 'Manual'")

config = picam2.create_video_configuration(
    main={"size": (1296, 972), "format": "RGB888"},
    controls=controls_dict
)
picam2.configure(config)

video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)  # Ensure directory exists

for h in range(video_number):
    filename = f"{video_dir}{HostName}_{UID}_{h+1:03d}.mp4"
    fourcc = cv2.VideoWriter_fourcc(*'mp4v')
    out = cv2.VideoWriter(filename, fourcc, Framerate, (1296, 972))
    picam2.start()
    start = time.time()
    while (time.time() - start) < video_duration and running:
        frame = picam2.capture_array()
        # Annotate frame
        text = f"{HostName}, {Framerate} fps, {dt.now().strftime('%Y-%m-%d %H:%M:%S')}"
        cv2.putText(frame, text, (10, 40), cv2.FONT_HERSHEY_SIMPLEX, 1, (0,0,255), 2, cv2.LINE_AA)
        out.write(frame)
        time.sleep(1/Framerate)
    picam2.stop()
    out.release()
    
    if not running:
        print("Exited early due to signal.")
        break