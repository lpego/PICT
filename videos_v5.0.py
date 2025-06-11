from picamera2 import Picamera2, Preview
from picamera2.encoders import H264Encoder, Quality
from libcamera import controls
from datetime import datetime
import signal
import time
import socket
import uuid
import os

# Setup
video_duration = 1800
video_number = 336
target_fps = 5
video_dir = "/home/pi/record/videos/"
os.makedirs(video_dir, exist_ok=True)

UID = datetime.now().strftime('%Y-%m-%d_%H-%M') + '_' + uuid.uuid4().hex[:4].upper()
HostName = socket.gethostname()

picam2 = Picamera2()
config = picam2.create_video_configuration(
    main={"size": (1296, 972), "format": "YUV420"},
    controls={
        "FrameRate": target_fps,
        "AfMode": controls.AfModeEnum.Continuous
    }
)
picam2.configure(config)

# picam2.configure(picam2.create_video_configuration())
encoder = H264Encoder()

# Signal handling
running = True
def handle_signal(sig, frame):
    global running
    print("Signal received, stopping...")
    running = False
signal.signal(signal.SIGINT, handle_signal)
signal.signal(signal.SIGTERM, handle_signal)

# Main loop
for h in range(video_number):
    filename = f"{video_dir}{HostName}_{UID}_{h+1:03d}.h264"
    print(f"Recording {filename}")

    # Start camera with overlay text
    picam2.start()
    picam2.set_controls({"FrameRate": target_fps})
    # picam2.start_recording(filename)
    picam2.start_recording(encoder, filename, quality=Quality.HIGH)

    start = time.time()

    while time.time() - start < video_duration and running:
        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M:%S")
        overlay_text = f"{HostName}, {target_fps} fps, {timestamp}"
        picam2.set_overlay_text(overlay_text)
        time.sleep(1)  # Update every second

    picam2.stop_recording()
    picam2.stop()

    print(f"Finished recording {filename}")

    if not running:
        break
