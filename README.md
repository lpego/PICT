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
sudo apt update 
sudo apt install -y python3-opencv python3-picamera2
```
It takes a while to compile... 

## Testing recording
Recoding works as expected, only thing the stack is a bit slow to start up, resulting in some delay from script launch to actual start of recording. 

Added `.sh` script for logging time and errors too, had to remove spaces in `time = [...]` assignment... 

Installing crontab
``crontab -e``
and paste at the bottom of the file: 
```
0 21 * * * sudo killall python
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 4 * * * /home/pi/start_video_v2.0.py
```

> [!NOTE]
> Leave `kilalll` command only here in `crontab`, do not put it in the `.sh` file. 

### Experimenting with camera focus
The raspberry Pi camera v3 has electromagnetic autofocus, fully supported in libcamera (https://www.raspberrypi.com/documentation/computers/camera_software.html). 

Autofocus set to continuous is *crazy* fast, it might impact resource usage if run constantly. Might be better to run an autofocus sweep every once in a while, setting 

> [!TIP]
> Pay attention that both `picamera2` and `licamera` have a control submodule, but the Afmode keys are encoded differently! 

Also implemented autofocus toggle on live preview. 

# Implementing live preview server
Using FastAPI and uvicorn to stream MJPEG via HTTP. 

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

Transfer over to the Pi the Python script `live_preview_v1.0.py`: 
```
scp live_preview_v1.0.py pi@192.168.137.148:/home/pi/
```

Start the live server with `uvicorn`: 
```
python -m uvicorn live_preview_v4:app --host 0.0.0.0 --port 8000
```

On a browser (e.g. Firefox) go to: `192.168.137.148:8000`

WORKS! Very basic and with some latency but not too bad. 
Attempting to make server restart itself upon changing preview parameters is a bit more tricky, does not do it automatically, needs more work. 

# Testing battery and storage efficiency
*Test 1 -- 09 Jun, 11pm, battery 30Ah at 100%*
Recording at 1296*972px@10fps, autofocus continuous. 
 - At 7:30 am, battery at 68% ... 
 - small mistake, forgo to to change the crontab, recorded using `start_video_v2.0.sh`... 
 - fixing at 7:30am, restarted recording with `start_video_v4.0.sh`.
 - Turned off at ~8am on Jun 11th, battery remaining 11%, `/dev/mcblk0p1` (28G total) is 28% full (7.4GB).

Writing `.mp4` is very storage efficient, but consumes a lot more power, would be better to directly write frames in `.h264` or `.avi`... 

# TODOs
Test for power and storage efficiency
 - It seems like recording .mp4 is far less power efficient on the RPi Zero than writing raw .h264 format... 
 - Running autofocus in "continuous" mode might also have an impact

 # Resources
  - Useful post with libcam video examples: https://www.raspberrypi.com/news/raspberry-pi-camera-module-more-on-video-capture/
  - Picamera2 manual: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
  - General RPi camera references: https://www.raspberrypi.com/documentation/computers/camera_software.html