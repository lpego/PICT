from datetime import datetime
import signal
import time
import socket
import uuid
import os
import cv2

from picamera2 import MappedArray, Picamera2
from picamera2.encoders import H264Encoder, Quality
from libcamera import controls

### Parameters declaration
video_duration = 1800
video_number = 336
target_fps = 5
video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)

UID = datetime.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

### Initialize Picamera2 custom config
picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={
        "size": (1296, 972),
        # "format": "YUV420"
        },
    controls={
        "FrameRate": target_fps,
        "AfMode": controls.AfModeEnum.Continuous
    }
)
picam2.configure(config)

# ### Basic config for testing
# picam2 = Picamera2()
# picam2.configure(picam2.create_video_configuration())

### Overlay parameters
colour = (0, 255, 0)
origin = (0, 30)
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
encoder = H264Encoder(10000000)

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
    # picam2.start()
    picam2.set_controls({"FrameRate": target_fps})
    start = time.time()
    picam2.start_recording(encoder, f"{video_dir}OverlayTest_{HostName}_{UID}_{h+1:03d}.h264", quality=Quality.HIGH)
    while (time.time() - start) < video_duration and running:
        time.sleep(0.1)
    
    picam2.stop_recording()
    
    # ### Basic event loop for testing
    # picam2.start_recording(encoder, f"{video_dir}OverlayTest_{HostName}_{UID}_{h+1:03d}.h264")
    # time.sleep(5)
    # picam2.stop_recording()

    print(f"Finished recording {filename}")

    if not running:
        break

picam2.stop()
