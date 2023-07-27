# install azure cli

# login to azure
az login

# create repository
az acr create --name containerizationtool --resource-group containerization-tool --sku Standard

# login to repository
password="password"
echo "${password}" | docker login -u containerizationtool --password-stdin containerizationtool.azurecr.io

# tag docker image
docker tag "container-test-ping.sh_image" "containerizationtool.azurecr.io/container-test-ping.sh_image:latest"

# push docker image
docker push "containerizationtool.azurecr.io/container-test-ping.sh_image:latest"

# create container instance
az container create \
  --resource-group <resource-group-name> \
  --name <container-name> \
  --image <docker-image-name> \
  --ports <port-number> \
  --cpu <cpu-value> \
  --memory <memory-value> \
  --registry-username <registry-username> \
  --registry-password <registry-password> \
  --dns-name-label <dns-name-label> \
  --environment-variables <key=value> \
  --location <azure-region>


# show container instance
az container show \
  --resource-group <resource-group-name> \
  --name <container-name> \
  --query instanceView.state

# delete container instance
az container delete \
  --resource-group <resource-group-name> \
  --name <container-name> \
  --yes

