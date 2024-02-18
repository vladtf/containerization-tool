#!/bin/bash
# Description: This script cleans up the test environment
# 
# Usage: ./clean.sh
#

# Save current directory
BIN_DIR=$(dirname "$0")

# Script variables
compose_file="$BIN_DIR/docker-compose.yaml"
test_network_name="mynetwork"

###############################################
# Do not modify anything below this line
###############################################

# Paths
prepare_script_path="$BIN_DIR/prepare.sh"
compose_file_path="$BIN_DIR/docker-compose.yaml"

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

# Stop and remove the test container
log_info "Stopping and removing the test containers"
container_ids=$(docker ps -a --filter "network=$test_network_name" -q)
log_info "Found containers: $container_ids"

# Loop through each container ID and stop, remove, and log the container details
for container_id in $container_ids; do
    (
        container_name=$(docker ps -f "id=$container_id" --format "{{.Names}}")
        image_id=$(docker inspect -f '{{ .Image }}' $container_id)

        log_info "Stopping and removing container: $container_name (ID: $container_id)"

        # Stop the container
        docker stop $container_id

        # Remove the container
        docker rm $container_id

        # Delete the corresponding image
        # log_info "Deleting image with ID: $image_id"
        # docker rmi $image_id
    ) &
done

# Wait for all containers to be stopped and removed
wait

# Remove the test network
log_info "Removing the test network"
docker network rm "$test_network_name" >/dev/null 2>&1

# Stop and remove docker-compose services
log_info "Stopping and removing Kafka and database"
docker-compose -f "$compose_file_path" down -v

# Log clean-up completion
log_success "Clean-up completed"
