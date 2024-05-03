#!/bin/bash

test_count=4
dockerfile_path=./Dockerfile
network_name=perf
image_name=performance-test

# Create a network
docker network create --driver bridge --opt com.docker.network.bridge.name=$network_name $network_name
# Check if the network is created
if [ $(docker network ls | grep $network_name | wc -l) -eq 0 ]; then
  echo "Network not created"
  exit 1
fi

# Check if dockerfile exists
if [ ! -f $dockerfile_path ]; then
  echo "Dockerfile not found"
  exit 1
fi

create_times=()
delete_times=()

echo "Starting create (build + run) performance test..."
create_total_time=0
for i in $(seq 1 $test_count); do
    start_time=$(date +%s%N) # capture start time in nanoseconds

    # Build the image
    docker build -t $image_name . -f $dockerfile_path

    # Run the container
    docker run -it -d --network $network_name --name $image_name $image_name

    end_time=$(date +%s%N) # capture end time in nanoseconds
    elapsed_create=$(echo "scale=3;($end_time - $start_time) / 1000000000" | bc)
    create_times+=($elapsed_create)
    
    ############################

    start_time=$(date +%s%N) # capture start time in nanoseconds

    docker stop $image_name
    docker rm $image_name

    end_time=$(date +%s%N) # capture end time in nanoseconds
    elapsed_delete=$(echo "scale=3;($end_time - $start_time) / 1000000000" | bc)
    delete_times+=($elapsed_delete)

    docker rmi $image_name

    echo "Test $i: Create time: $elapsed_create seconds, Delete time: $elapsed_delete seconds"
done

echo "Create times: ${create_times[@]}"
echo "Delete times: ${delete_times[@]}"


# Clean up network at the end
docker network rm $network_name
