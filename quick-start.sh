#!/bin/bash

# save current directory
BIN_DIR=$(dirname $0)

# check if prepare.sh was sourced
if [ -z "$PREPARE_SH_SOURCED" ]; then
    echo "prepare.sh must be sourced before running this script"
    exit 1
fi

# Container name
test_container="my-ubuntu"

# Source prepare.sh
source "$BIN_DIR/prepare.sh"
if [ $? -ne 0 ]; then
    echo "failed to source prepare.sh"
    exit 1
fi

# check if kafka is running
docker inspect kafka > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # start kafka
    docker-compose -f "$BIN_DIR/docker-compose.yaml" up -d
else
    log_success "kafka already running"
fi

# check if test network exists
docker network inspect mynetwork > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # create test network
    docker network create mynetwork
else
    log_success "mynetwork already exists"
fi

# check if test container exists
docker inspect "$test_container" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # remove test container
    docker rm -f "$test_container" > /dev/null 2>&1
else
    log_success "$test_container does not exist"
fi

# build test container
build_logs=$(docker build -t my-ubuntu -f "$BIN_DIR/test/ubuntu/Dockerfile" "$BIN_DIR/test/ubuntu" 2>&1)
if [ $? -ne 0 ]; then
    log_error "build failed"
    log_error "$build_logs"
    exit 1
else
    log_success "build succeeded"
fi

# start test container
run_logs=$(docker run -d --network=mynetwork --name "$test_container" my-ubuntu 2>&1)
if [ $? -ne 0 ]; then
    log_error "run failed"
    log_error "$run_logs"
    exit 1
else
    log_success "run succeeded"
fi

# check if test container is running
docker inspect "$test_container" | grep '"Running": true' > /dev/null 2>&1
if [ $? -ne 0 ]; then
    log_error "$test_container is not running"
    exit 1
else
    log_success "$test_container is running"
fi
