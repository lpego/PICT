from picamera2 import Picamera2
from time import time

picam2 = Picamera2()
picam2.start()

# for i in range(30):
#     metadata = picam2.capture_metadata()
#     print("Frame", i, "has arrived")
#     print(f"Current Lens Position is: {metadata.get('LensPosition', 'N/A'):.2f}")

for focus in [1.0, 2.0, 3.0, 4.0, 5.0, 6.0, 7.0, 8.0, 9.0, 10.0]:
    print(f"Setting focus to {focus}")
    picam2.set_controls({"LensPosition": focus})
    time.sleep(1)  # Let lens settle
    metadata = picam2.capture_metadata()
    print(f"Current Lens Position is: {metadata.get('LensPosition', 'N/A'):.2f}")