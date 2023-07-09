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
log_info "Starting clean-up script"

# Stop and remove the monitoring script
log_info "Stopping monitoring script"
pkill -f "monitor-docker-traffic.py"

# Stop and remove the test container
log_info "Stopping and removing the test container"
docker stop "$test_container_name" >/dev/null 2>&1
docker rm "$test_container_name" >/dev/null 2>&1

# Remove the test network
log_info "Removing the test network"
docker network rm "$test_network_name" >/dev/null 2>&1

# Stop and remove Kafka
log_info "Stopping and removing Kafka"
docker-compose -f "$kafka_compose_file_path" down -v

# Remove the test container image
log_info "Removing the test container image"
docker rmi "$test_container_name" >/dev/null 2>&1

# Log clean-up completion
log_info "Clean-up completed"


# TODO: stop also frontend and backend