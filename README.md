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
Recoding works as expected, only thing the stack is a bit slow to start up, resulting in some dealy from script launch to actual start of recording. 

Added `.sh` script for logging time and errors too, had to remove spaces in `time = [...]` assignment... 

Installing crontab
``crontab -e``
and paste at the bottom of the file: 
```
0 21 * * * sudo killall python
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 6 * * * /home/pi/start_video_v2.0.py
```

[!NOTE]
Leave `kilalll` command only here in `crontab`, do not put it in the `.sh` file. 



# Implementing live preview server
Using FastAPI to stream MJPEG via HTTP. 

Installing dependencies: 
<!-- ```
sudo apt update
sudo apt install python3-pip
pip3 install fastapi uvicorn
``` -->
```
sudo apt update
sudo apt install python3-fastapi python-uvicorn
```

Start stream with `live_preview_v1.0.py`. 
[...]

# TODOs
Recording .mp4 has several problems: 
 - If the recording script gets killed externally, the last video (i.e. the one being recorded) will be "corrupted", because the file ending or something similar does not get written. 
 - It seems like it is far less power efficient on the RPi Zero than writing raw .h264 format... 