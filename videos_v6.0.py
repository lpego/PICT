from datetime import datetime
import signal
import time
import socket
import uuid
import os
import cv2

from picamera2 import MappedArray, Picamera2
from picamera2.encoders import H264Encoder

### Parameters declaration
video_duration = 1800
video_number = 336
target_fps = 5
video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)

UID = datetime.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

### Initialize Picamera2
# # picam2 = Picamera2()
# config = picam2.create_video_configuration(
#     main={"size": (1296, 972), "format": "YUV420"},
#     controls={
#         "FrameRate": target_fps,
#         "AfMode": controls.AfModeEnum.Continuous
#     }
# )
# picam2.configure(config)

picam2 = Picamera2()
picam2.configure(picam2.create_video_configuration())

### Overlay parameters
colour = (0, 255, 0)
origin = (0, 30)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2


def apply_timestamp(request):
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin, font, scale, colour, thickness)


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

    # # Start camera with overlay text
    # picam2.start()
    # picam2.set_controls({"FrameRate": target_fps})
    # # picam2.start_recording(filename)
    # picam2.start_recording(encoder, filename, quality=Quality.HIGH)

    # start = time.time()

    # while time.time() - start < video_duration and running:
    #     timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    #     overlay_text = f"{HostName}, {target_fps} fps, {timestamp}"
    #     picam2.set_overlay(overlay_text)
    #     time.sleep(1)  # Update every second

    # picam2.stop_recording()
    # picam2.stop()
    
    picam2.start_recording(encoder, f"OverlayTest_{filename}")
    time.sleep(5)
    picam2.stop_recording()

    print(f"Finished recording {filename}")

    if not running:
        break
