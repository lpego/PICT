#!/bin/bash

# Idle threshold in seconds (10 minutes)
IDLE_THRESHOLD=$((10 * 60))

# Session ID for user 'pi'
SESSION_ID=$(loginctl | grep ' pi ' | awk '{print $1}')

# Live preview service name
LIVE_PREVIEW_SERVICE="live-preview.service"

# Recording script path
RECORDING_SCRIPT="/home/pi/start_videos_v6.0.sh"

# Convert logind IdleSinceHint to seconds
IDLE_MICRO=$(loginctl show-session "$SESSION_ID" -p IdleSinceHint | cut -d= -f2)
CURRENT_EPOCH_MICRO=$(($(date +%s) * 1000000))

# Time idle in seconds
IDLE_SECONDS=$(( (CURRENT_EPOCH_MICRO - IDLE_MICRO) / 1000000 ))

if [ "$IDLE_SECONDS" -ge "$IDLE_THRESHOLD" ]; then
  echo "[INFO] System idle for $IDLE_SECONDS seconds. Stopping preview and starting recording..."

  systemctl stop "$LIVE_PREVIEW_SERVICE"
  bash "$RECORDING_SCRIPT"
else
  echo "[INFO] System has been idle for $IDLE_SECONDS seconds. Waiting..."
fi
