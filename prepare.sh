#!/bin/bash

# flag to indicate this script was sourced
export PREPARE_SH_SOURCED=true

# save current directory
BIN_DIR=$(dirname $0)

# declare alias to connect to test container
alias go-test='docker exec -it my-ubuntu bash'

# source python virtual environment
source $BIN_DIR/utils/myenv/bin/activate

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Log directory
export LOG_DIR="$BIN_DIR/logs"
export LOG_FILE="$LOG_DIR/script.log"
mkdir -p "$LOG_DIR"

# Logging functions
log_success() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[SUCCESS] $1"
    echo -e "${GREEN}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >> "$LOG_FILE"
}

log_error() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[ERROR] $1"so

    echo -e "${RED}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >> "$LOG_FILE"
}

log_warning() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[WARNING] $1"
    echo -e "${YELLOW}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >> "$LOG_FILE"
}
