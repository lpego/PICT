# Presets for Raspberry Pi Camera v3
# ---
# Preset 1: Full HD, 30 FPS, Auto Focus
# Framerate = 30
# Resolution = (1920, 1080)
# Focus = "Auto"
# ---
# Preset 2: 720p, 15 FPS, Manual Focus (close-up)
# Framerate = 15
# Resolution = (1280, 720)
# Focus = "Manual"
# Focus_distance = 100.0  # Adjust for your subject distance (0–1024)
# ---
# Preset 3: 4:3 Aspect, 10 FPS, Auto Focus
# Framerate = 10
# Resolution = (1296, 972)
# Focus = "Auto"
# ---

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
Resolution = (1296, 972)  # Set the desired resolution as (width, height)
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
    main={"size": Resolution, "format": "RGB888"},
    controls=controls_dict
)
picam2.configure(config)

video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)  # Ensure directory exists

for h in range(video_number):
    filename = f"{video_dir}{HostName}_{UID}_{h+1:03d}.h264"  # Changed extension to .h264
    fourcc = cv2.VideoWriter_fourcc(*'H264')  # Use H264 codec
    out = cv2.VideoWriter(filename, fourcc, Framerate, Resolution)
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