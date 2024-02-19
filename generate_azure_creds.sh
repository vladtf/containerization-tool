#!/bin/bash
# Description: This script creates an Azure service principal and replaces the credentials in a docker-compose file
#
# Usage: ./generate_azure_creds.sh
#

servicePrincipalName="containerization_backend"
subscriptionName="Azure for Students"
pathToDockerCompose="docker-compose.yaml"

##############################
# DO NOT EDIT BELOW THIS LINE
##############################
BIN_DIR=$(dirname "$0")
log_script_path="$BIN_DIR/scripts/logs.sh"

# Source logging script
echo "Sourcing logging script: $log_script_path"
source "$log_script_path"

log_info "Logging in to Azure CLI..."

# put the tenant id here if needed
az login # --tenant <tenant-id>

# check if service principal already exists and if so, delete it
spExists=$(az ad sp list --display-name $servicePrincipalName --query "[?displayName=='$servicePrincipalName'].appId" --output tsv)
if [ -n "$spExists" ]; then
    log_warning "Service principal already exists, deleting it..."
    az ad sp delete --id $spExists
fi

# get subscription id by name
subscriptionId=$(az account list --query "[?name=='$subscriptionName'].id" --output tsv)

# if subscription id is not found list all subscriptions and exit
if [ -z "$subscriptionId" ]; then
    log_warning "Subscription not found, listing all subscriptions..."
    subscriptions=$(az account list --query "[].{name:name, subscriptionId:id}" --output table)
    log_warning "Please restart the script and provide one of the following subscription names:"
    log_warning "$subscriptions"
    exit 1
fi

log_info "Creating service principal for subscription $subscriptionName with name $servicePrincipalName"

principal=$(az ad sp create-for-rbac --name $servicePrincipalName --role Contributor --scopes /subscriptions/$subscriptionId)

log_info "Service principal created successfully with the following details:"
echo $principal | jq

log_info "Do you want the credentials to be replaced in $pathToDockerCompose? (y/n)"
read replaceInDockerCompose
if [ "$replaceInDockerCompose" == "y" ]; then
    # check if docker-compose.yml exists
    if [ ! -f "$pathToDockerCompose" ]; then
        log_error "$pathToDockerCompose not found, please make sure you are in the correct directory"
        exit 1
    fi

    clientId=$(echo $principal | jq -r '.appId')
    clientSecret=$(echo $principal | jq -r '.password')
    tenantId=$(echo $principal | jq -r '.tenant')
    sed -i "s/AZURE_CLIENT_ID:.*/AZURE_CLIENT_ID: $clientId/" $pathToDockerCompose
    sed -i "s/AZURE_CLIENT_SECRET:.*/AZURE_CLIENT_SECRET: $clientSecret/" $pathToDockerCompose
    sed -i "s/AZURE_TENANT_ID:.*/AZURE_TENANT_ID: $tenantId/" $pathToDockerCompose

    # check if credentials were replaced successfully (check if secret is in the file)
    if ! grep -q $clientSecret $pathToDockerCompose; then
        log_error "Credentials were not replaced in $pathToDockerCompose"
        exit 1
    fi

    log_info "Credentials replaced in $pathToDockerCompose. You can now run docker-compose up"
fi
