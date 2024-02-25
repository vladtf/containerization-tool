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

servicePrincipalName="containerization_backend"
subscriptionName="Azure for Students"

###############################################
# Do not modify anything below this line
###############################################

# Paths
logging_script_path="$BIN_DIR/scripts/logs.sh"
compose_file_path="$BIN_DIR/docker-compose.yaml"


# Source prepare.sh
echo "Sourcing logging script: $logging_script_path"
source "$logging_script_path"
if [ $? -ne 0 ]; then
    echo "Failed to source logging script: $logging_script_path"
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
log_info "Stopping and removing containers using docker-compose"
docker-compose -f "$compose_file_path" down -v

# Delete service principal from Azure
log_info "Deleting service principal from Azure"
az ad sp delete --id $(az ad sp list --display-name $servicePrincipalName --query "[].appId" --output tsv)

# Removing credentials form docker compose file
log_info "Removing credentials from docker-compose file"
sed -i 's/AZURE_CLIENT_ID:.*/AZURE_CLIENT_ID: CHANGEME/' $compose_file_path
sed -i 's/AZURE_CLIENT_SECRET:.*/AZURE_CLIENT_SECRET: CHANGEME/' $compose_file_path
sed -i 's/AZURE_TENANT_ID:.*/AZURE_TENANT_ID: CHANGEME/' $compose_file_path

# Log clean-up completion
log_success "Clean-up completed"
