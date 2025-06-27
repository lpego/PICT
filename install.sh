#!/bin/bash

### Change to the install.sh directory, update repo
cd "$(dirname "$0")"

echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Pulling latest changes from repository..."

git pull

### Substituting existing crontab with default
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Applying default crontab..."

crontab crontab

### Installing systemd management of live server
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Installing live server..."

cp -r live-preview /home/pi/

sudo cp live-preview/live-preview.service /etc/systemd/system/live-preview.service

sudo systemctl daemon-reexec
sudo systemctl daemon-reload
sudo systemctl enable live-preview.service
sudo systemctl start live-preview.service

### installing autostart
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Installing autostart with idle check..."

chmod +x autostart/idle-check.sh
sudo cp autostart/idle-check.service /etc/systemd/system/idle-check.service
sudo cp autostart/idle-check.timer /etc/systemd/system/idle-check.timer

sudo systemctl daemon-reexec
sudo systemctl enable idle-check.timer
sudo systemctl start idle-check.timer

### Moving video scripts
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Installing video recording scripts..."

cp videos*.py /home/pi/
cp start_video*.sh /home/pi/
chmod +x /home/pi/start_video*.sh

### Finish message
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"
echo "Install complete!"
echo "### ~~~~~~~~~~~~~~~~~~~~~~~~~ ###"