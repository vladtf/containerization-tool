#!/bin/bash
# Description: This script starts the container manager script

BIN_DIR=$(dirname "$0")

###############################################
# Do not modify anything below this line
###############################################

# Paths
containers_manager_script_name="containers-manager.py"
containers_manager_script_path="$BIN_DIR/monitoring/$containers_manager_script_name"
prepare_script_path="$BIN_DIR/prepare.sh"

# Function to start container manager
start_containers_manager() {
    log_info "Starting containers manager"
    python3 "$containers_manager_script_path" &
}

# Function to stop container manager
stop_containers_manager() {
    log_warning "Stopping containers manager"
    for pid in $(ps aux | grep "$containers_manager_script_name" | grep -v grep | awk '{print $2}'); do
        log_info "Stopping monitoring (PID: $pid)"
        kill -s INT "$pid"
    done
}

# Function to handle Ctrl+C
interrupt_handler() {
    stop_containers_manager
    exit 0
}

# Check if prepare.sh was sourced
if [ -z "$PREPARE_SH_SOURCED" ]; then
    echo "prepare.sh must be sourced before running this script"
    exit 1
fi

# Source prepare.sh
echo "Sourcing prepare.sh"
source "$prepare_script_path"
if [ $? -ne 0 ]; then
    echo "Failed to source prepare.sh"
    exit 1
fi

# Stop containers manager if it is already running
stop_containers_manager

# Start monitoring initially
start_containers_manager

# Set up interrupt handler for Ctrl+C
trap interrupt_handler SIGINT

# Watch for changes in the monitoring script and restart it
while inotifywait -e close_write "$containers_manager_script_path"; do
    log_warning "Detected changes in containers manager script. Restarting..."
    stop_containers_manager
    start_containers_manager
done
