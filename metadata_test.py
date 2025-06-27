from picamera2 import Picamera2

picam2 = Picamera2()
picam2.start()

for i in range(30):
    metadata = picam2.capture_metadata()
    print("Frame", i, "has arrived")
    print(f"Current Lens Position is: {metadata.get('LensPosition', 'N/A'):.2f}")