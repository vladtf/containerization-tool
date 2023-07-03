#!/bin/bash
# Description: This script starts the monitoring of the container forwarding rules

BIN_DIR=$(dirname "$0")

###############################################
# Do not modify anything below this line
###############################################

# Paths
monitoring_forwarding_rules_script_name="monitor-forwarding-rules.py"
monitoring_forwarding_rules_script_path="$BIN_DIR/monitoring/$monitoring_forwarding_rules_script_name"
prepare_script_path="$BIN_DIR/prepare.sh"

# Function to start monitoring
start_monitoring() {
    log_info "Starting monitoring"
    python3 "$monitoring_forwarding_rules_script_path" &
}

# Function to stop monitoring
stop_monitoring() {
    log_warning "Stopping Forwarding Rules Monitoring"
    for pid in $(ps aux | grep "$monitoring_forwarding_rules_script_name" | grep -v grep | awk '{print $2}'); do
        log_info "Stopping monitoring (PID: $pid)"
        kill -9 "$pid"
    done
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

# Start monitoring initially
start_monitoring

# Watch for changes in the monitoring script and restart it
while inotifywait -e close_write "$monitoring_forwarding_rules_script_path"; do
    log_warning "Detected changes in monitoring script. Restarting..."
    stop_monitoring
    start_monitoring
done
