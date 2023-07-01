#!/bin/bash

# save current directory
BIN_DIR=$(dirname $0)


# check if kafka is running
docker inspect kafka > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # start kafka
    docker-compose -f $BIN_DIR/docker-compose.yaml up -d
else
    echo "kafka already running"
fi

# check if test network exists
docker network inspect mynetwork > /dev/null 2>&1
if [ $? -ne 0 ]; then
    # create test network
    docker network create mynetwork
else
    echo "mynetwork already exists"
fi

# check if test container exists
docker inspect my-ubuntu > /dev/null 2>&1
if [ $? -eq 0 ]; then
    # remove test container
    docker rm -f my-ubuntu
else
    echo "my-ubuntu does not exist"
fi

# build test container
build_logs=$(docker build -t my-ubuntu -f $BIN_DIR/test/ubuntu/Dockerfile $BIN_DIR/test/ubuntu 2>&1)
if [ $? -ne 0 ]; then
    echo "build failed"
    echo "$build_logs"
    exit 1
else
    echo "build succeeded"
fi

# start test container
run_logs=$(docker run -d --network=mynetwork --name my-ubuntu my-ubuntu 2>&1)
if [ $? -ne 0 ]; then
    echo "run failed"
    echo "$run_logs"
    exit 1
else
    echo "run succeeded"
fi

# check if test container is running
docker inspect my-ubuntu | grep '"Running": true' > /dev/null 2>&1
if [ $? -ne 0 ]; then
    echo "my-ubuntu is not running"
    exit 1
else
    echo "my-ubuntu is running"
fi

