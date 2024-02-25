#!/bin/bash
# Description: This script starts environment required for monitoring
#
# Usage: ./quick-start.sh
#

# Save current directory
BIN_DIR=$(dirname "$0")

# Script variables
docker_compose_file_path="$BIN_DIR/docker-compose.yaml"
generate_credentials_script_path="$BIN_DIR/generate_azure_creds.sh"
test_container_name="my-ubuntu"
test_network_name="mynetwork"

###############################################
# Do not modify anything below this line
###############################################

# Paths
test_container_path="$BIN_DIR/test/ubuntu"
test_container_dockerfile_path="$test_container_path/Dockerfile"
logs_script_path="$BIN_DIR/scripts/logs.sh"

# Source logging script
echo "Sourcing logging script: $logs_script_path"
source "$logs_script_path"
if [ $? -ne 0 ]; then
    echo "Failed to source logging script: $logs_script_path"
    exit 1
fi

# Log script start
log_info "Starting script"

# Check if credentials in the compose file are set
log_info "Checking Compose file for credentials"
if grep -q "AZURE_CLIENT_SECRET:.*CHANGEME" "$docker_compose_file_path"; then
    log_error "Running the script to generate credentials"
    "$generate_credentials_script_path"
else
    log_success "Credentials are set"
fi

# Check if Kafka is running
log_info "Checking Compose status"
if ! docker-compose -f "$docker_compose_file_path" ps kafka | grep "Up" >/dev/null 2>&1; then
    # Start Kafka
    log_info "Starting Compose"
    docker-compose -f "$docker_compose_file_path" up -d --build
else
    log_success "Compose is already running"
fi

# Check if the test network exists
log_info "Checking test network"
docker network inspect "$test_network_name" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    # Create the test network
    log_info "Creating test network"
    docker network create --driver bridge --opt com.docker.network.bridge.name="$test_network_name" "$test_network_name"
else
    log_success "$test_network_name already exists"
fi

# Check if the test container exists
log_info "Checking test container"
docker inspect "$test_container_name" >/dev/null 2>&1
if [ $? -eq 0 ]; then
    # Remove the test container
    log_info "Removing existing test container"
    docker rm -f "$test_container_name" >/dev/null 2>&1
else
    log_success "$test_container_name does not exist"
fi

# Build the test container
log_info "Building test container"
build_logs=$(docker build -t "$test_container_name" -f "$test_container_dockerfile_path" "$test_container_path" 2>&1)
if [ $? -ne 0 ]; then
    log_error "build failed"
    log_error "$build_logs"
    exit 1
else
    log_success "build succeeded"
fi

# Start the test container
log_info "Starting test container"
run_logs=$(docker run -d --cap-add NET_ADMIN --network="$test_network_name" --name "$test_container_name" "$test_container_name" 2>&1)
if [ $? -ne 0 ]; then
    log_error "run failed"
    log_error "$run_logs"
    exit 1
else
    log_success "run succeeded"
fi

# Check if the test container is running
log_info "Checking test container status"
docker inspect "$test_container_name" | grep '"Running": true' >/dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "$test_container_name is not running"
    exit 1
else
    log_success "$test_container_name is running"
fi

# Log script end
log_success "Quick start script completed successfully. You can now access the page at http://localhost:3000"
