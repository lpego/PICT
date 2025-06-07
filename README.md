# PICT
A new an improved version of PICT (Droissart et al. 2021), based on Bookworm

# Installing the OS
Using Raspberry Pi Images v1.9.4 - https://downloads.raspberrypi.org/imager/imager_latest.exe 

Selecting these values in RPi Imager: 
 - Model: RPi Zero
 - OS version: Pi OS lite (32-bit) - no desktop, no dependencies

Selecting additional settings before flashing: 
 - Username: pi ; password: raspberry
 - WiFi SSID: PICT_network_1 ; password: pollinators1
 - wireless LAN country: CH
 - locale: EU/ Zurich
In "Services" tab: 
 - Enable SSH; use password authentication

Works, confirmed. 

# Checking v3 RPi camera
Both libcamera and rpicam libraries are pre-installed. See https://www.raspberrypi.com/documentation/computers/camera_software.html

Cannot get a live preview, no X-view device available on headless Pi. 

Can save stills though: 
``rpicam-jpeg --output test.jpg``

# Python script
Copied over ``videos_v1.2.py`` from PICT_v2 repo: 
```
scp videos_v1.2.py pi@[IP]:/home/pi
```

Testing imports, found that ``cv2`` and ``picamera2`` are not preinstalled (Python 3.11 is though). 

Installing missing dependencies: 
```
sudo apt install -y python3-opencv python3-picamera2
```
It takes a while to compile... 

## Testing recording
