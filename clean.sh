#!/bin/bash

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

# Stop python scripts
log_info "Stopping python scripts"
kill_python_script(){
    script_name=$1
    for pid in $(ps aux | grep "$script_name" | grep -v grep | awk '{print $2}'); do
        log_info "Stopping monitoring (PID: $pid)"
        kill "$pid"
    done
}

kill_python_script "containers-manager.py"
kill_python_script "monitor-docker-traffic.py"
kill_python_script "monitor-forwarding-rules.py"

# Kill tmux sessions
log_info "Killing tmux sessions"
tmux kill-session -t "monitoring-session" >/dev/null 2>&1


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


# Stop backend
log_info "Stopping backend"
backend_pid=$(ps aux | grep "containerization-tool/backend" | grep -v grep | awk '{print $2}')
for pid in $backend_pid; do
    log_info "Stopping backend (PID: $pid)"
    kill "$pid"
done


# Stop frontend
log_info "Stopping frontend"
frontend_pid=$(ps aux | grep "containerization-tool/frontend" | grep -v grep | awk '{print $2}')
for pid in $frontend_pid; do
    log_info "Stopping frontend (PID: $pid)"
    kill "$pid"
done


# Stop and remove Kafka
log_info "Stopping and removing Kafka and database"
docker-compose -f "$compose_file_path" down -v


# Log clean-up completion
log_success "Clean-up completed"
