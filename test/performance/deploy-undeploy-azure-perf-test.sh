#!/bin/bash

test_count=10
dockerfile_path=./Dockerfile
resource_group_name=manualtest
ecr_name=manualtest
container_name=manualtest
container_instance_name=manualtest
location=uksouth
image_name=manualtest

# build the image
echo "Building docker image..."
docker build -t $image_name . -f $dockerfile_path

# login to azure
# az login

# check if resource group exists
exists=$(az group exists --name $resource_group_name)
if [ $exists == "true" ]; then
  echo "Resource group already exists"
else
  echo "Resource group does not exist"
  # create resource group
  az group create --name $resource_group_name --location $location
fi

create_times=()
delete_times=()

echo "Starting deploy (create + delete) performance test..."
create_total_time=0
for i in $(seq 1 $test_count); do
  start_time=$(date +%s%N) # capture start time in nanoseconds

  # create repository
  echo "Creating repository..."
  az acr create --name $ecr_name --resource-group $resource_group_name --sku Standard

  # login to repository
  echo "Logging in to repository..."
  token=$(az acr login --name $ecr_name --expose-token --output json | jq -r .accessToken)
  docker login $ecr_name.azurecr.io -u "00000000-0000-0000-0000-000000000000" -p $token

  # tag docker image
  echo "Tagging docker image..."
  docker tag $image_name "$ecr_name.azurecr.io/$image_name:latest"

  # push docker image
  echo "Pushing docker image..."
  docker push "$ecr_name.azurecr.io/$image_name:latest"

  # create container instance
  echo "Creating container instance..."
  az container create \
    --resource-group $resource_group_name \
    --name $container_instance_name \
    --image "$ecr_name.azurecr.io/$image_name:latest" \
    --registry-username "00000000-0000-0000-0000-000000000000" \
    --registry-password "${token}" \
    --ports 80

  end_time=$(date +%s%N) # capture end time in nanoseconds
  elapsed_create=$(echo "scale=3;($end_time - $start_time) / 1000000" | bc)
  create_times+=($elapsed_create)

  ############################

  start_time=$(date +%s%N) # capture start time in nanoseconds

  # delete container instance
  echo "Deleting container instance..."
  az container delete \
    --resource-group $resource_group_name \
    --name $container_instance_name \
    --yes

  end_time=$(date +%s%N) # capture end time in nanoseconds
  elapsed_delete=$(echo "scale=3;($end_time - $start_time) / 1000000" | bc)
  delete_times+=($elapsed_delete)

  
  # delete repository
  echo "Deleting repository..."
  az acr delete --name $ecr_name --resource-group $resource_group_name --yes

  # delete image
  echo "Deleting image..."
  docker rmi $image_name

  echo "Test $i: Create time: $elapsed_create ms, Delete time: $elapsed_delete ms"


  # sleep for 10 seconds
  echo "Sleeping for 10 seconds..."
  sleep 10
done

# delete resource group
echo "Deleting resource group..."
az group delete --name $resource_group_name --yes

echo "Create times: ${create_times[@]}"
echo "Delete times: ${delete_times[@]}"
