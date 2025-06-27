⚠ **These are the development notes** ⚠

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

# Python scripts
Copied over ``videos_v1.2.py`` from PICT_v2 repo: 
``` bash
scp videos_v1.2.py pi@[IP]:/home/pi
```

Testing imports, found that ``cv2`` and ``picamera2`` are not preinstalled (Python 3.11 is though). 

Installing missing dependencies: 
``` bash
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
``` bash
sudo apt update
sudo apt install python3-fastapi python-uvicorn
```

Transfer over to the Pi the Python script `live_preview_v5.py`: 
``` bash
scp live_preview/live_preview_v5.py pi@192.168.137.148:/home/pi/
```

Start the live server with `uvicorn`: 
``` bash
python -m uvicorn live-preview/live_preview_v5:app --host 0.0.0.0 --port 8000
```

On a browser (e.g. Firefox) go to: `192.168.137.148:8000`

WORKS! Very basic and with some latency but not too bad. 
Attempting to make server restart itself upon changing preview parameters is a bit more tricky, does not do it automatically, needs more work. 

## Managing uvicorn server with systemd
Uses `live_preview/live_preview_v5.py` and above. Need to set up a dedicated service, copy `live_preview/live-preview.service` to `home/pi` and move it in the systemd directory: 
``` bash
sudo mv live-preview.service /etc/systemd/system/live-preview.service
```
Stop the daemon, add the new service and restart: 
``` bash
sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable live-preview.service
sudo systemctl start live-preview.service
```
The uvicorn server should now be controlled by: 
``` bash
sudo systemctl restart live-preview.service
sudo systemctl stop live-preview.service
sudo journalctl -u live-preview.service -f  # View logs
```

⚠ CAUTION: it needs to be able to run sudo systemctl [...] without password, the following achieves that but this can be dangerous and a security risk, even though it's limited to the live-preview service. 

Add user `pi` to sudo-ers, to not prompt for password every time. Open sudo-ers file:
``` bash
sudo visudo
```
Add `pi ALL=NOPASSWD: /bin/systemctl restart live-preview.service` at the end. 

### Fixing automatically restarting camera preview
The uvicorn server does not automatically restart correctly when camera parameters are updated on the preview GUI. 

Adding a landing page while the server reloads (https://github.com/lpego/PICT/commit/c00fa8d5749bef8e9e46e06003e30f1a0b9627d6), and that listens to response from the now reloaded camera preview page (https://github.com/lpego/PICT/commit/59890d504c5c62db4db59a2471b49bd778600a53). 

✅ At commit https://github.com/lpego/PICT/commit/a704bcf0c4eaff84f605dd813e2928d3fef8e92c the live preview service functions correctly. 

# Auto-starting the live preview at boot, and auto-record after a delay.
I want the Raspberry Pi to start recording automatically (with default settings) if there's no user activity for a certain time. 

We implement this, we run a service, `autostart/idle-check.service` that calls the script `autostart/idle-check.sh` in order to track time since last activity (i.e. mostly SSH interactions in this case). 
We also run a timer `autostart/idle_check.timer` that calls again every 1 minute `idle-check.service`. 

If after 10 minutes (parameter set in `idle-check.sh`) no activity is detected, then `idle-check.sh` will: 
 - stop the live-preview service
 - start recording by calling `/home/pi/start_videos_v6.0.sh` (or whichever `.sh` script)

Steps to install:

1. `scp -r autostart pi@192.168.137.71:/home/pi/`
1. `chmod +x autostart/idle-check.sh`
1. `sudo mv autostart/idle-check.service /etc/systemd/system/`
1. `sudo mv autostart/idle-check.timer /etc/systemd/system`
1. 
``` bash
sudo systemctl daemon-reexec
sudo systemctl enable idle-check.timer
sudo systemctl start idle-check.timer
```

## Handle recording already in progress
We need to add some logic to the scripts launching the recording to make sure we do not start another recording while another is in progress (as that would return an error because the resource, i.e. the camera is busy). 

We write a lockfile at the start of the `.sh` scripts and remove it at the end, as follows: 
``` bash
# Lock file to prevent multiple instances
LOCKFILE="/tmp/recording.lock"
if [ -f "$LOCKFILE" ]; then
    echo "[INFO] Recording already in progress. Skipping."
    exit 0
fi
touch "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT
```

> [!NOTE]
> If the Pi dies unexpectedly (i.e. low battery, forcibly disconnected, etc), the lockfile is removed from `/tmp` and will trigger autorecording after 10 minutes at next boot. 

# Testing battery and storage efficiency

> [!NOTE]
> The base system image has a footprint of 2.5GB on `/dev/mcblk0p2`, ~10% fo the total available size. The space available for videos is ~26.5 GBs.

## Test 1 - 09 Jun, 11pm, battery 30Ah at 100%
Recording at 1296*972px@10fps, autofocus continuous. 
 - At 7:30 am, battery at 68% ... 
 - small mistake, forgot to to change the crontab, recorded using `start_video_v2.0.sh`... 
 - fixing at 7:30am, restarted recording with `start_video_v4.0.sh`.
 - Turned off at ~8am on Jun 11th, battery remaining 11%, `/dev/mcblk0p1` (28G total) is 28% full (7.4GB).

Writing `.mp4` is very storage efficient, but consumes a lot more power, would be better to directly write frames in `.h264` or `.avi`... 

## Test 2 - 15 Jun, 11am, battery 30Ah at 99%
Recording at 1296*972px@10fps, recording in `.h264`, autofocus continuous; editing crontab: 
``` 
0 21 * * * sudo killall python
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 4 * * * /home/pi/start_video_v6.0.py
```

### End of test
*Interim results:* Jun 15, 6pm: battery 74%; storage 29% (7.5 GB / 20 GB) -- that's a ~3.7% battery consumed per hour of recording, or ~1.11A per hour of recording.

Files excerpts in `/tests/Test1/`

*Last recording:* 17 Jun, 7:34am; *Total hours recorded*: 15 Jun, 11-21 = 10h; 16 Jun, 6-21 = 15h; 17 Jun, 6-7:30 = 1.5h.

*Storage:* 7.24GB free of 28.4GB tot; that's a total of 21.16GB occupied. Average video size (i.e. set tp 30 minutes length) is: 332.69 MB. That's 665.38 MB per hour of recording. 

**TOT = 26.5h** ; that's ~3.73% battery consumed per hour of recording, or 1.13A per hour of recording. 

## Test 3 - 16 Jun, 6am, on mains power - with Raspberry Pi camera v3 **wide**
Recording at 1296*972px@10fps, recording in `.h264`, autofocus continuous; crontab: 
```
0 21 * * * sudo killall python | true
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 6 * * * /home/pi/start_video_v6.0.sh
```
This test was to see if the wide version of the camera has any differences in file size or handling; does not seem so. Will try to record at actual wide proportions next test. 

## Test 4 - 21 Jun, 5:15pm, mains power - with Raspberry Pi camera v3 **wide**
Recording at 1536*864px@10fps, recording in `.h264`, focus fixed @ 4.0 (~25cm); crontab: 
```
0 21 * * * sudo killall python | true
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 6 * * * /home/pi/start_video_v6.2.sh
```

*Interim results:* 22 Jun, 9:20am, 8.4GB used (31% total); average file size: 371.75 MB. 

Average file size obtained with:
```bash
find . -name "*.h264" -type f -printf "%s\n" | awk 'BEGIN{total=0; count=0} {total+=$1; count++} END {if (count>0) print total/count/1024/1024 " MB"; else print "0 MB"}'
```

### End of test
Files excerpts in `/tests/Test4/`; 

*Last recording:* 23 Jun, ; *Total hours recorded*: 21 Jun, 17:15-21 = 3.75h; 22 Jun, 6-21 = 15h; 23 Jun, 6-18:20 = 12.3h.

*Storage:* 0GB free of 29GB tot; Average video size (i.e. set tp 30 minutes length) is: 246.09 MB. That's 492.18 MB per hour of recording. 

**TOT = 31.05h**; that's ~3.22% battery consumed per hour of recording, or 0.96A per hour of recording.

## Test 5 - 22 Jun, 9:20am, battery 30Ah at 100%
Recording at 1296*972px@10fps, recording in `.h264`, focus fixed @ 4.0 (~25cm); crontab: 
``` 
0 21 * * * sudo killall python
1 21 * * * sudo ifconfig wlan0 down
55 5 * * * sudo reboot
0 6 * * * /home/pi/start_video_v6.1.py
```
### End of test
Files excerpts in `/tests/Test5/`; blurry as heck, not sure why, set the same parameter as in the preview and that was fine... 

*Last recording:* 24 Jun, 6:02am; *Total hours recorded*: 22 Jun, 9:20-21 = 11:40h; 23 Jun, 6-21 = 15h; 24 Jun, 6-6:02 ~ 0h.

*Storage:* 7.9GB free of 29GB tot; that's a total of 21GB occupied. Average video size (i.e. set tp 30 minutes length) is: 307.45 MB. That's 614.9 MB per hour of recording. 

**TOT = 36.6h** ; that's ~2.73% battery consumed per hour of recording, or 0.83A per hour of recording.

# Testing direct recording (uncompressed)
Testing `.h264` recording, with script `video_v5.0.py`

Running into issues while trying to timestamp the frames as they are recorded... see commit https://github.com/lpego/PICT/commit/f32bcaf0ff76e81e8741a304a5a9534ed3dbb48b

Looking for inspiration here: https://github.com/raspberrypi/picamera2/blob/main/examples/timestamped_video.py-- works a treat!

Implemented in `videos_v6.0.py`, functional state with commit https://github.com/lpego/PICT/commit/8d0598134fa3e588ff735d8e5ead461cb3c52d34 

Fixed event handling loop: https://github.com/lpego/PICT/commit/a4c268f6f0c5717faa0e7d5ae4ae189783ae92f9

Working on the framerate: trying to get the framerate into `picamera2` config as easily as possible: #105c2bf7ad3cead537078757899a2d92261b0555

> [!IMPORTANT]
> When saving `.h264` files, ffmpeg / ffprobe will report an _incorrect_ FPS! This is due to the fact that `.h264` is not really a container and ffmepg cannot guess the framerate...

# Cloning image and shrinking for distribution
Win32DiskImager: input name of file where to save image (`.img`), slecet 'boot' partition of SD card, skip hash, do "Read". 

Shrink image with https://github.com/Drewsif/PiShrink : 
 - Follow instructions for WSL: https://github.com/Drewsif/PiShrink#windows-instructions
 - Shrink image according to instructions here: https://github.com/Drewsif/PiShrink#usage
    - I run: `sudo pishrink.sh -avz PICTv3.0.img`
    - Shrunk from ~28GB (the block-by-block copy of the whole SD card) to 1.2 GB. 

Get an error when flashing to SD card with Raspberry Pi imager: "Image size is not multiple of 512 bytes"...

Attempting to solve with: https://github.com/Drewsif/PiShrink/issues/195#issuecomment-1602477659 - re-gzipped manually, shared. 

## Testing flashing image to new SD card
Using the exact same model and size of SD card as original image cloned. 

Flashing with Raspberry Pi Imager, selecting "no custom configuration" (as all configs are already written in the image). Writes and verifies correctly. 

Booting Raspberry Pi... Takes quite a while to stop blinking. 

Connecting via SSH (gets automatically assigned a different IP address than original image, thankfully) works fine. 

File system successfully expanded on first boot! 

# Investigating why manual focus parameters seem to be ignored
While in the live preview server the manual focus parameter seem to work as expected, in the recording scripts it is ignored: even though the trigger for manual focus is accepted, the value for lens position is not. 

Testing with custom recording script that cycles a few manual focus parameters: `manual_focus_test.py`. 

Working off of the examples in the [manual](https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf), pages 32-33, specifically: 

``` python
from picamera2 import Picamera2
from libcamera import controls

picam2 = Picamera2()
picam2.start(show_preview=True)
picam2.set_controls({"AfMode": controls.AfModeEnum.Manual, "LensPosition": 0.0})
```

Testing with stripped down version of main recording script (`videos_v6.2.py`), and seems to work. 
The issue seemed to be that we need to *start* the camera before configuring it. 

# TODOs
 - Need to test different quality presets and their impact on power consumption.
 - Running autofocus in "continuous" mode might also have an impact... 
    - Implement a periodical focus sweep instead. 
    - Implement setting an autofocus range, so that it doesn't focus on infinity.
 - Maybe test other encoders for power consumption? 
 - It seems like recording .mp4 is far less power efficient on the RPi Zero than writing raw .h264 format... ✅

# Resources
  - Useful post with libcam video examples: https://www.raspberrypi.com/news/raspberry-pi-camera-module-more-on-video-capture/
  - Picamera2 manual: https://datasheets.raspberrypi.com/camera/picamera2-manual.pdf
  - General RPi camera references: https://www.raspberrypi.com/documentation/computers/camera_software.html