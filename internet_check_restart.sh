#!/bin/bash

# Function to log messages
log_message() {
    echo "[$(date '+%Y-%m-%d %H:%M:%S')] $1"
}

# Function to check internet connection
check_internet() {
    ping -c 1 8.8.8.8 > /dev/null 2>&1
    return $?
}

# Check internet connection
if check_internet; then
    log_message "Internet connection is available."
else
    log_message "No internet connection. Restarting the device..."
    sudo reboot
fi