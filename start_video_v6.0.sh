#!/bin/bash

# # Close preview server
sudo systemctl stop live-preview.service

# Start Python script for video recording and redirect output (STD.OUT & STD.ERR)
# must be in the same directory as the .py script
time=`date +"%Y%m%d_%H%M"`
nohup python videos_v6.0.py > record/log_videos_${time}.out 2>&1 &