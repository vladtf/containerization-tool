#!/bin/bash

# Flag to indicate this script was sourced
export PREPARE_SH_SOURCED=true

# Save current directory
BIN_DIR=$(dirname "$0")

# Declare alias to connect to the test container
alias go-test='docker exec -it my-ubuntu bash'

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
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_error() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[ERROR] $1"

    echo -e "${RED}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_warning() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[WARNING] $1"
    echo -e "${YELLOW}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_info() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[INFO] $1"
    echo -e "$timestamp - $log_message"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

# Create virtual environment
VENV_DIR="$BIN_DIR/.venv"
REQUIREMENTS_FILE="$BIN_DIR/requirements.txt"

# Check if .venv directory exists
if [ ! -d "$VENV_DIR" ]; then
    log_warning "Virtual environment not found. Creating virtual environment..."
    python3 -m venv "$VENV_DIR"

    if [ $? -ne 0 ]; then
        log_error "Failed to create virtual environment"
        exit 1
    else
        log_success "Virtual environment created"
    fi

    log_info "Activating virtual environment"
    source "$VENV_DIR/bin/activate"
    if [ $? -ne 0 ]; then
        log_error "Failed to activate virtual environment"
        exit 1
    else
        log_success "Virtual environment activated"
    fi

    # Install requirements
    if [ -f "$REQUIREMENTS_FILE" ]; then
        log_info "Installing requirements"
        pip install -r "$REQUIREMENTS_FILE"
        if [ $? -ne 0 ]; then
            log_error "Failed to install requirements"
            exit 1
        else
            log_success "Requirements installed"
        fi
    else
        log_error "Requirements file '$REQUIREMENTS_FILE' not found."
        log_error "Please make sure to create the requirements file and try again."
        exit 1
    fi
else
    log_info "Activating virtual environment"
    source "$VENV_DIR/bin/activate"
    log_success "Virtual environment activated"

    log_info "Installing requirements"
    pip install -r "$REQUIREMENTS_FILE"

    if [ $? -ne 0 ]; then
        log_error "Failed to install requirements"
        exit 1
    else
        log_success "Requirements installed"
    fi
fi
