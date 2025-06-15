#!/bin/bash

# Lock file to prevent multiple instances
LOCKFILE="/tmp/recording.lock"
if [ -f "$LOCKFILE" ]; then
    echo "[INFO] Recording already in progress. Skipping."
    exit 0
fi
touch "$LOCKFILE"
trap "rm -f $LOCKFILE" EXIT

# # Close preview server
sudo systemctl stop live-preview.service

# Start Python script for video recording and redirect output (STD.OUT & STD.ERR)
# must be in the same directory as the .py script
time=`date +"%Y%m%d_%H%M"`
mkdir -p record
nohup python videos_v6.0.py > record/log_videos_${time}.out 2>&1 &