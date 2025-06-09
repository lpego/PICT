#!/bin/bash

# # Ensure that no other processes are using the camera
# sudo killall python || true

# Start Python script for video recording and redirect output (STD.OUT & STD.ERR)
# must be in the same directory as the .py script
time=`date +"%Y%m%d_%H%M"`
nohup python videos_v2.0.py > log_videos_${time}.out 2>&1 &