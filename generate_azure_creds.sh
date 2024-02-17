#!/bin/bash
# Description: TODO


servicePrincipalName="containerization_backend"
subscriptionName="Azure for Students"
pathToDockerCompose="docker-compose.yaml"

az login

# check if service principal already exists and if so, delete it
spExists=$(az ad sp list --display-name $servicePrincipalName --query "[?displayName=='$servicePrincipalName'].appId" --output tsv)
if [ -n "$spExists" ]; then
    echo "Service principal already exists, deleting it..."
    az ad sp delete --id $spExists
fi


# get subscription id by name
subscriptionId=$(az account list --query "[?name=='$subscriptionName'].id" --output tsv)

# if subscription id is not found list all subscriptions and exit
if [ -z "$subscriptionId" ]; then
    echo "Subscription not found, listing all subscriptions..."
    subscriptions=$(az account list --query "[].{name:name, subscriptionId:id}" --output table)
    echo "\n\e[33mPlease restart the script and provide one of the following subscription names:\e[0m"
    echo "$subscriptions"
    exit 1
fi

echo "Creating service principal for subscription $subscriptionName with name $servicePrincipalName"

principal=$(az ad sp create-for-rbac --name $servicePrincipalName --role Contributor --scopes /subscriptions/$subscriptionId)

echo -e "\e[32mService principal created successfully with the following details:\e[0m"
echo $principal | jq

echo -e "\e[35mDo you want the credentials to be replaced in $pathToDockerCompose? (y/n)\e[0m"
read replaceInDockerCompose
if [ "$replaceInDockerCompose" == "y" ]; then
    # check if docker-compose.yml exists
    if [ ! -f "$pathToDockerCompose" ]; then
        echo "$pathToDockerCompose not found, please make sure you are in the correct directory"
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
        echo -e "\e[31mCredentials were not replaced in $pathToDockerCompose\e[0m"
        exit 1
    fi

    echo -e "\e[32mCredentials replaced in $pathToDockerCompose. You can now run docker-compose up\e[0m"
fi
