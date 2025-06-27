from datetime import datetime
import signal
import time
import socket
import uuid
import os
import cv2
from picamera2 import Picamera2
from picamera2 import MappedArray
from picamera2.encoders import H264Encoder, Quality
from libcamera import controls

### Parameters declaration
video_duration = 1800
video_number = 336
resolution = (1536, 864)  # Set the desired resolution as (width, height), WIDE format
target_fps = 10
focus = "Manual"  # Set to "Auto" or "Manual"
focus_distance = 4  # Only used if Focus is "Manual"; 0 (infinity) and 10.0 (approx. 10cm); default is 0.5 (focus at ~1m))
video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)

UID = datetime.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

### Signal handling
running = True
def handle_signal(sig, frame):
    global running
    print("Signal received, stopping...")
    running = False
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

###
picam2 = Picamera2()
picam2.start(show_preview=False)
picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})

### Event loop
for h in range(video_number):
    filename = f"{video_dir}FocusTest-{HostName}_{UID}_{h+1:03d}.h264"
    print(f"Recording {filename}")

    ### Start camera with custom config and overlay text
    # picam2.start()
    start = time.time()
    picam2.start_recording(encoder, f"{video_dir}FocusTest-{HostName}_{UID}_{h+1:03d}.h264", quality=Quality.HIGH)
    while (time.time() - start) < video_duration and running:
        time.sleep(0.1)
    
    picam2.stop_recording()

    print(f"Finished recording {filename}")

    if not running:
        break

picam2.stop()