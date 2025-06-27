# PICT
A new an improved version of PICT ([Droissart *et al.*, 2021](https://besjournals.onlinelibrary.wiley.com/doi/full/10.1111/2041-210X.13618)), based on Bookworm OS. 

# Hardware
In this guide I assume you are using a [Raspberry Pi Zero W](https://www.raspberrypi.com/products/raspberry-pi-zero-w/) and a [Raspberry Pi Camera v3](https://www.raspberrypi.com/products/camera-module-3/) (with IR filter, non-wide). 

For more detailed hardware specifications, take a look at ['How to build PICT' guide](https://zenodo.org/records/6301001), most of the recommendations still apply. 

# Installation
## Quickstart
The easiest way to get started is to use one of the pre-built images I provide.

You can download image ISOs here (requires permission): https://drive.google.com/drive/u/2/folders/136YHJ19of67geJv1VAqPn2JNwlM1lIbM

Use a software like [Raspberry Pi Imager](https://downloads.raspberrypi.org/imager/imager_latest.exe) or [Balena Etcher](https://etcher.balena.io/) to flash one of these images to an SD card. 

> [!NOTE]
> If using [Raspberry Pi Imager](https://downloads.raspberrypi.org/imager/imager_latest.exe), when prompted write the image without modifying the configuration. 

Once flashing is complete, insert the SD card in your Pi ad connect to power; you might have to wait for up to 10 minutes for the first boot to complete. 

> [!NOTE]
> The OS images provided should auto-expand to fill all available space on the SD card; is that doesn't happen for some reason, you can use the [`raspi-config`](https://www.raspberrypi.com/documentation/computers/configuration.html#expand-filesystem) utility to do that on the Pi directly. 

## Installing the OS
Alternatively, you can also start from a stock Raspberry Pi image and follow the steps below.

Using Raspberry Pi Images v1.9.4 - https://downloads.raspberrypi.org/imager/imager_latest.exe 

Selecting these values in RPi Imager: 
 - Model: RPi Zero
 - OS version: Pi OS lite (32-bit) - no desktop, no dependencies

Selecting additional settings before flashing: 
 - Username: `pi` ; password: `raspberry`
 - WiFi SSID: `PICT_network_1` ; password: `pollinators1`
 - wireless LAN country: `CH`
 - locale: `EU/Zurich`
In "Services" tab: 
 - Enable SSH; use password authentication

# Connecting to the Pi
In the following section I assume the configuration outlined above, that assumes you are using a laptop or a smartphone as hotspot with this parameters: 
 - WiFi SSID: `PICT_network_1`
 - password: `pollinators1`
 - band: `2.4GHz`

The Pi is already configured to look for this network and connect to it. 

How you can verify if the Pi is connected to your hotspot varies depending on your device, but the steps are generally something like: 
 - Windows: Wi-Fi settings > Mobile hotspot
 - Android: Settings > W-Fi & Internet > Hotspot & tethering > Wi-Fi hotspot
    - Alternatively, you can download [NetAnalyzer](https://techet.net/netanalyzer/) and use the "LAN scan" function

What you are after is the IP address assigned to your Pi, as you will need this for the next steps.

## Live preview server
At boot, the Pi should automatically start a server showing the camera stream, which is useful to check framing and adjust parameters. 

You should be presented with a screen like this: 
![live-server](assets/live-server.png)

## Connect via SSH

# Changelog
*v3.1.0* - working towards a cleaned version of the repo to be cloned directly on the Pi.

[...]

*v3.0.2* - implementing managing of preview server and recording via system services

*v3.0.1* - implementation of live preview server based on `uvicorn`.

*v3.0.0* - re-hash of older software based on Pi OS Buster; the reason is that RPi camera v3 is incompatible with the `picamera` stack... 