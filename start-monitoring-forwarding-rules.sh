#!/bin/bash
# Description: This script starts the monitoring of the container forwarding rules

BIN_DIR=$(dirname "$0")

###############################################
# Do not modify anything below this line
###############################################

# Paths
monitoring_forwarding_rules_script_path="$BIN_DIR/monitoring/monitor-forwarding-rules.py"
prepare_script_path="$BIN_DIR/prepare.sh"

# Function to start monitoring
start_monitoring() {
    log_info "Starting monitoring"
    python3 "$monitoring_forwarding_rules_script_path" &
    MONITORING_PID=$!  # Store the PID of the monitoring process
}

# Function to stop monitoring
stop_monitoring() {
    if [[ -n "$MONITORING_PID" ]]; then
        log_error "Stopping monitoring"
        kill "$MONITORING_PID"
        wait "$MONITORING_PID" 2>/dev/null  # Suppress any error messages
        unset MONITORING_PID
    fi
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
