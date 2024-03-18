# build the image
docker build -t manual-test .

# create a network
docker network create --driver bridge --opt com.docker.network.bridge.name=manual-test-net manual-test-net

# run the container
docker run -it -d --network manual-test-net --name manual-test manual-test

# see the logs
docker ps | grep manual-test
docker logs <container_id>

# check the traffic messages
docker exec -it traffic_monitor bash
tcpdump -i manual-test-net


# login to azure
az login

# create resource group
az group create --name manual-test --location uksouth

# create repository
az acr create --name manualtest --resource-group manual-test --sku Standard

# login to repository
token=$(az acr login --name manualtest --expose-token --output json | jq -r .accessToken)
docker login manualtest.azurecr.io -u "00000000-0000-0000-0000-000000000000" -p $token

# tag docker image
docker tag "manual-test" "manualtest.azurecr.io/manual-test:latest"

# push docker image
docker push "manualtest.azurecr.io/manual-test:latest"

# create container instance
az container create \
  --resource-group "manual-test" \
  --name "container-test-ping-sh" \
  --image "manualtest.azurecr.io/manual-test:latest" \
  --registry-username "00000000-0000-0000-0000-000000000000" \
  --registry-password "${token}" \
  --ports 80


# show container instance
az container show \
  --resource-group "manual-test" \
  --name "container-test-ping-sh" \
  --query instanceView.state


# show container instance logs
az container logs \
  --resource-group "manual-test" \
  --name "container-test-ping-sh"

# delete container instance
az container delete \
  --resource-group "manual-test" \
  --name "container-test-ping-sh" \
  --yes

# show container instance list
az container list \
    --resource-group "manual-test" \
    --output table

# delete repository
az acr delete --name manualtest --resource-group manual-test --yes

# delete resource group
az group delete --name manual-test --yes

# remove container
docker ps | grep manual-test
docker rm -f <container_id>

# remove network
docker network rm manual-test-net

# delete image
docker rmi manual-test