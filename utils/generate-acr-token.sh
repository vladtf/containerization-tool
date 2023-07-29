#!/bin/bash

# Function to log in to Azure and get ACR access token
ACR_NAME="containerizationtool"
ACR_LOGIN_SERVER="${ACR_NAME}.azurecr.io"

echo "Logging in to Azure..."
az login

echo "Generating ACR access token..."
ACCESS_TOKEN=$(az acr login --name $ACR_NAME --expose-token | jq -r '.accessToken')

if [ -z "$ACCESS_TOKEN" ]; then
    echo "Failed to get ACR access token. Exiting..."
    exit 1
fi

echo "Logging in to ACR..."
docker login $ACR_LOGIN_SERVER -u 00000000-0000-0000-0000-000000000000 -p $ACCESS_TOKEN
