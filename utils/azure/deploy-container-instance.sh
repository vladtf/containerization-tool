# install azure cli

# login to azure
az login

# create resource group
az group create --name containerization-tool --location uksouth

# create repository
az acr create --name containerizationtool --resource-group containerization-tool --sku Standard

# login to repository
password="password"
echo "${password}" | docker login -u containerizationtool --password-stdin containerizationtool.azurecr.io

# tag docker image
docker tag "manual-test" "containerizationtool.azurecr.io/manual-test:latest"

# push docker image
docker push "containerizationtool.azurecr.io/manual-test:latest"

# create container instance
az container create \
  --resource-group "containerization-tool" \
  --name "container-test-ping-sh" \
  --image "containerizationtool.azurecr.io/manual-test:latest" \
  --registry-username "containerizationtool" \
  --registry-password "${password}" \
  --ports 80

#   --cpu 1 \
#   --memory 1 \
#   --location <azure-region>
#   --dns-name-label <dns-name-label> \
#   --environment-variables <key=value> \
#   --registry-username <registry-username> \
#   --registry-password <registry-password> \


# show container instance
az container show \
  --resource-group "containerization-tool" \
  --name "container-test-ping-sh" \
  --query instanceView.state


# show container instance logs
az container logs \
  --resource-group "containerization-tool" \
  --name "container-test-ping-sh"

# delete container instance
az container delete \
  --resource-group "containerization-tool" \
  --name "container-test-ping-sh" \
  --yes

# show container instance list
az container list \
    --resource-group "containerization-tool" \
    --output table

az container show \
  --resource-group "containerization-tool" \
  --name "my-ubuntu" > container.json


# show logs
az container logs --resource-group "containerization-tool" --name "container-test-ping-sh"


az container attach --resource-group "containerization-tool" --name "container-test-ping-sh"

az container exec --resource-group "containerization-tool" --name "container-test-ping-sh" --exec-command "/bin/bash"