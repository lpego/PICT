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

# ### Initialize Picamera2, as per example
# picam2 = Picamera2()
# picam2.start(show_preview=False)
# picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})

### Parameters declaration
video_duration = 5
video_number = 1
resolution = (1536, 864)  # Set the desired resolution as (width, height), WIDE format
target_fps = 10
focus = "Manual"  # Set to "Auto" or "Manual"
focus_distance = 4  # Only used if Focus is "Manual"; 0 (infinity) and 10.0 (approx. 10cm); default is 0.5 (focus at ~1m))
video_dir = "/home/pi/record/videos/focus_test/"
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
picam2.start()

# time.sleep(1)  # Allow time for the camera to configure

### Overlay parameters
colour = (255, 0, 0)
origin1 = (5, 30)
origin2 = (5, 60)
font = cv2.FONT_HERSHEY_SIMPLEX
scale = 1
thickness = 2
current_lens_position = "N/A"

### Define overlay function, apply to callback
def apply_timestamp(request):
    timestamp = time.strftime("%Y-%m-%d %X")
    with MappedArray(request, "main") as m:
        cv2.putText(m.array, timestamp, origin1, font, scale, colour, thickness)
        cv2.putText(m.array, f"LensPosition: {current_lens_position}", origin2, font, scale, colour, thickness)

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

### Cycle through lens positions
for focus in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]:
    print(f"Setting focus to {focus}m")
    picam2.set_controls({"LensPosition": focus})
    time.sleep(1)  # Let lens settle

    for h in range(video_number):
        filename = f"{video_dir}FocusTest_LensPosition_{focus}-{HostName}_{UID}_{h+1:03d}.h264"
        print(f"Recording {filename}")

        # Start recording
        picam2.start_recording(encoder, filename, quality=Quality.HIGH)

        # Wait a few frames to ensure metadata is available
        time.sleep(0.5)
        try:
            meta = picam2.capture_metadata(timeout=5)
            current_lens_position = f"{meta.get('LensPosition', 'N/A'):.2f}"
        except Exception as e:
            print(f"Warning: Failed to get metadata for lens position: {e}")
            current_lens_position = "N/A"

        # Record for duration
        start = time.time()
        while (time.time() - start) < video_duration and running:
            time.sleep(0.1)

        picam2.stop_recording()
        print(f"Finished recording {filename}")

        if not running:
            break

picam2.stop()