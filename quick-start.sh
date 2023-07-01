#!/bin/bash

# Save current directory
BIN_DIR=$(dirname "$0")

# Script variables
kafka_compose_file="$BIN_DIR/docker-compose.yaml"
test_container_name="my-ubuntu"
test_network_name="mynetwork"

###############################################
# Do not modify anything below this line
###############################################

# Paths
prepare_script_path="$BIN_DIR/prepare.sh"
kafka_compose_file_path="$BIN_DIR/docker-compose.yaml"
test_container_path="$BIN_DIR/test/ubuntu"
test_container_dockerfile_path="$test_container_path/Dockerfile"

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

# Log script start
log_info "Starting script"

# Check if Kafka is running
log_info "Checking Kafka status"
if ! docker-compose -f "$kafka_compose_file_path" ps kafka | grep "Up" >/dev/null 2>&1; then
    # Start Kafka
    log_info "Starting Kafka"
    docker-compose -f "$kafka_compose_file_path" up -d
else
    log_success "Kafka is already running"
fi

# Check if the test network exists
log_info "Checking test network"
docker network inspect "$test_network_name" >/dev/null 2>&1
if [ $? -ne 0 ]; then
    # Create the test network
    log_info "Creating test network"
    docker network create "$test_network_name"
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

# Start the monitoring script
log_info "Starting monitoring script"
python "$BIN_DIR/monitoring/monitor-docker-traffic.py"

# Log script end
log_info "Script execution completed"
