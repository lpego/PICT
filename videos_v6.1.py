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
resolution = (1296, 972)  # Set the desired resolution as (width, height)
target_fps = 10
focus = "Auto"  # Set to "Auto" or "Manual"
focus_distance = 4  # Only used if Focus is "Manual"; 0 (infinity) and 10.0 (approx. 10cm); default is 0.5 (focus at ~1m))
video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)

UID = datetime.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

### Initialize Picamera2 custom config
picam2 = Picamera2()

if focus == "Auto":
    picam2.set_controls({"AfMode": controls.AfModeEnum.Continuous})
elif focus == "Manual":
    lens_position = focus_distance if 0 <= focus_distance <= 10 else .5
    picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": lens_position})
else:
    raise ValueError("Focus must be either 'Auto' or 'Manual'")

picam2.video_configuration.controls.FrameRate = target_fps
picam2.video_configuration.main.size = resolution
picam2.video_configuration.main.format = "YUV420"
picam2.video_configuration.align()
picam2.configure("video")

### Overlay parameters
colour = (0, 0, 255)
origin = (5, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2

### Define overlay function, apply to callback
def apply_timestamp(request):
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)

picam2.pre_callback = apply_timestamp

### Initialise encoder, w/ bitrate
encoder = H264Encoder()

### Signal handling
running = True
def handle_signal(sig, frame):
    global running
    print("Signal received, stopping...")
    running = False
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

### Event loop
for h in range(video_number):
    filename = f"{video_dir}{HostName}_{UID}_{h+1:03d}.h264"
    print(f"Recording {filename}")

    ### Start camera with custom config and overlay text
    picam2.start()
    start = time.time()
    picam2.start_recording(encoder, f"{video_dir}AutoFocus-{HostName}_{UID}_{h+1:03d}.h264", quality=Quality.HIGH)
    while (time.time() - start) < video_duration and running:
        time.sleep(0.1)
    
    picam2.stop_recording()

    print(f"Finished recording {filename}")

    if not running:
        break

picam2.stop()
