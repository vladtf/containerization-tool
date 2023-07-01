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

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# check if kafka is running
docker inspect kafka > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # start kafka
    docker-compose -f "$BIN_DIR/docker-compose.yaml" up -d
else
    echo -e "${GREEN}kafka already running${NC}"
fi

# check if test network exists
docker network inspect mynetwork > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # create test network
    docker network create mynetwork
else
    echo -e "${GREEN}mynetwork already exists${NC}"
fi

# check if test container exists
docker inspect "$test_container" > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # remove test container
    docker rm -f "$test_container"
else
    echo -e "${GREEN}$test_container does not exist${NC}"
fi

# build test container
build_logs=$(docker build -t my-ubuntu -f "$BIN_DIR/test/ubuntu/Dockerfile" "$BIN_DIR/test/ubuntu" 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}build failed${NC}"
    echo -e "$build_logs"
    exit 1
else
    echo -e "${GREEN}build succeeded${NC}"
fi

# start test container
run_logs=$(docker run -d --network=mynetwork --name "$test_container" my-ubuntu 2>&1)
if [ $? -ne 0 ]; then
    echo -e "${RED}run failed${NC}"
    echo -e "$run_logs"
    exit 1
else
    echo -e "${GREEN}run succeeded${NC}"
fi

# check if test container is running
docker inspect "$test_container" | grep '"Running": true' > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo -e "${RED}$test_container is not running${NC}"
    exit 1
else
    echo -e "${GREEN}$test_container is running${NC}"
fi
