#!/bin/bash

# save current directory
BIN_DIR=$(dirname "$0")

# Script variables
prepare_script="$BIN_DIR/prepare.sh"
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

# check if prepare.sh was sourced
if [ -z "$PREPARE_SH_SOURCED" ]; then
    echo "prepare.sh must be sourced before running this script"
    exit 1
fi

# Source prepare.sh
source "$prepare_script_path"
if [ $? -ne 0 ]; then
    echo "failed to source prepare.sh"
    exit 1
fi

# check if kafka is running
docker-compose -f "$kafka_compose_file_path" ps kafka > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # start kafka
    docker-compose -f "$kafka_compose_file_path" up -d
else
    log_success "kafka already running"
fi

# check if test network exists
docker network inspect "$test_network_name" > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # create test network
    docker network create "$test_network_name"
else
    log_success "$test_network_name already exists"
fi

# check if test container exists
docker inspect "$test_container_name" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # remove test container
    docker rm -f "$test_container_name" > /dev/null 2>&1
else
    log_success "$test_container_name does not exist"
fi

# build test container
build_logs=$(docker build -t "$test_container_name" -f "$test_container_dockerfile_path" "$test_container_path" 2>&1)
if [ $? -ne 0 ]; then
    log_error "build failed"
    log_error "$build_logs"
    exit 1
else
    log_success "build succeeded"
fi

# start test container
run_logs=$(docker run -d --network="$test_network_name" --name "$test_container_name" "$test_container_name" 2>&1)
if [ $? -ne 0 ]; then
    log_error "run failed"
    log_error "$run_logs"
    exit 1
else
    log_success "run succeeded"
fi

# check if test container is running
docker inspect "$test_container_name" | grep '"Running": true' > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "$test_container_name is not running"
    exit 1
else
    log_success "$test_container_name is running"
fi

# start monitoring script
python "$BIN_DIR/monitor-docker-traffic.py"
