import json
import logging
import subprocess
from dataclasses import dataclass, asdict

import docker
from azure.containerregistry import ContainerRegistryClient
from azure.core.exceptions import ResourceNotFoundError
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import ContainerGroupSubnetId
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.network import NetworkManagementClient
from azure.mgmt.network.models import VirtualNetwork, Subnet, Delegation
from azure.mgmt.resource import ResourceManagementClient
from azure.mgmt.subscription import SubscriptionClient

from kafka.kafka_client import DataClassEncoder

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Disable the Azure SDK logging for HTTP requests
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)


@dataclass
class AzureContainer:
    id: int
    name: str
    status: str
    image: str
    instance_id: str
    instance_name: str

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DataClassEncoder)

    @classmethod
    def from_dict(cls, param):
        return cls(**param)

def login_to_azure_as_service_principal(tenant_id, client_id, client_secret):
    # Login to Azure using the service principal
    cmd = f"az login --service-principal --username {client_id} --password {client_secret} --tenant {tenant_id}"
    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
    
    if result.returncode != 0:
        raise Exception(f"Failed to login to Azure using the service principal. Error: {result.stderr}")
    
    logger.info("Logged in to Azure using the service principal.")
    
    return result.stdout

def get_acr_access_token(acr_name):
    cmd = f"az acr login --name {acr_name} --expose-token --output json"
    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if result.returncode == 0:
        token_output = json.loads(result.stdout)
        access_token = token_output["accessToken"]

        return access_token
    else:
        raise Exception(
            f"Failed to get ACR access token. Error: {result.stderr}")


def login_to_acr(acr_url) -> docker.DockerClient:
    # Get the ACR access token
    access_token = get_acr_access_token(acr_url)

    # Get the docker client
    docker_client = docker.from_env()

    # Login to the ACR
    docker_client.login(username="00000000-0000-0000-0000-000000000000",
                        password=access_token,
                        registry=acr_url)

    logger.info(f"Logged in to ACR {acr_url}.")

    return docker_client


def push_image_to_acr(container_data: AzureContainer, acr_url):
    # Login to the ACR
    docker_client = login_to_acr(acr_url)

    # Check if the image exists locally
    image = docker_client.images.get(container_data.image)
    logger.info(f"Image {container_data.image} found locally.")

    # Tag the image with the ACR URL
    acr_image_name = f"{acr_url}/{container_data.name}:latest"
    image.tag(acr_image_name)

    # Push the image to the ACR
    resp = docker_client.images.push(repository=acr_image_name,
                                     stream=True,
                                     decode=True)

    # Print the push response
    for line in resp:
        if "error" in line:
            logger.error(f"Error while pushing image: {line}")
            raise Exception(f"Error while pushing image: {line}")
        elif "status" in line:
            logger.info(f"Pushing image: {line}")

    logger.info(f"Image {container_data.image} pushed to ACR {acr_url}.")
    return acr_image_name


def get_subscription_id(subscription_name, credentials):
    # Create a SubscriptionClient to get the subscription ID
    subscription_client = SubscriptionClient(credentials)

    # Get a list of subscriptions associated with the identity
    subscriptions = list(subscription_client.subscriptions.list())

    # Find the subscription with the given name
    for subscription in subscriptions:
        if subscription.display_name == subscription_name:
            return subscription.subscription_id

    # Return None if the subscription with the given name is not found
    return None

def get_all_subscriptions(credentials):
    # Create a SubscriptionClient to get the subscription ID
    subscription_client = SubscriptionClient(credentials)

    # Get a list of subscriptions associated with the identity
    subscriptions = list(subscription_client.subscriptions.list())

    return subscriptions


def assign_owner_role_to_current_user(subscription_id, resource_group, acr_server, credentials):
    # Create a ResourceManagementClient to assign the owner role to the current user
    resource_client = ResourceManagementClient(credentials, subscription_id)

    # Get the current user's object ID
    cmd = "az ad signed-in-user show --output json"
    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)
    if result.returncode == 0:
        user_output = json.loads(result.stdout)
        user_object_id = user_output["objectId"]
    else:
        raise Exception(f"Failed to get the current user's object ID. Error: {result.stderr}")

    # Assign the owner role to the current user
    resource_client.role_assignments.create(
        scope=f"/subscriptions/{subscription_id}/resourceGroups/{resource_group}/providers/Microsoft.ContainerRegistry/registries/{acr_server}",
        role_definition_id="/subscriptions/00000000-0000-0000-0000-000000000000/providers/Microsoft.Authorization/roleDefinitions/b24988ac-6180-42a0-ab88-20f7382dd24c",
        principal_id=user_object_id
    )

    logger.info(f"Assigned the owner role to the current user for ACR {acr_server}.")


def get_acr_url(subscription_id, resource_group, acr_server, credentials, location):
    acr_client = ContainerRegistryManagementClient(credentials, subscription_id)

    try:
        acr = acr_client.registries.get(resource_group, acr_server)
        logger.debug(f"Container registry '{acr_server}' exists in the Azure subscription.")
        return acr.login_server
    except ResourceNotFoundError:
        logger.warning(f"Container registry '{acr_server}' not found in the Azure subscription.")

        create_params = {
            "location": location,
            "sku": {
                "name": "Standard"
            },
            "admin_user_enabled": True
        }

        logger.info(f"Creating container registry '{acr_server}' in the Azure subscription...")

        # Create the container registry
        registry = acr_client.registries.begin_create(
            resource_group,
            acr_server,
            create_params
        ).result()

        # TODO: after create of the ACR, it is required to assign owner role to the current user
        # assign_owner_role_to_current_user(subscription_id, resource_group, acr_server, credentials)

        acr = acr_client.registries.get(resource_group, acr_server)

        logger.info(f"Container registry '{acr_server}' created in the Azure subscription.")
        return acr.login_server


def get_azure_instance_data(azure_container: AzureContainer, subscription_id: str, resource_group: str,
                            credentials) -> dict:
    azure_instance = azure_container.to_dict()

    # Get the container instance using the ID
    container_client = ContainerInstanceManagementClient(credentials, subscription_id)
    container_group = container_client.container_groups.get(resource_group, azure_container.name)

    azure_instance["instance_id"] = container_group.id
    azure_instance["instance_name"] = container_group.name
    azure_instance["instance_status"] = container_group.containers[0].instance_view.current_state.state
    azure_instance["instance_ip"] = container_group.ip_address.ip if container_group.ip_address else None
    azure_instance["instance_ports"] = [port.port for port in
                                        container_group.ip_address.ports] if container_group.ip_address else None
    azure_instance["instance_image"] = container_group.containers[0].image
    azure_instance["instance_start_time"] = container_group.containers[0].instance_view.current_state.start_time

    return azure_instance


def get_all_azure_container_instances(credentials, subscription_id: str) -> list:
    # Get the container instances
    container_client = ContainerInstanceManagementClient(credentials, subscription_id)
    container_groups = container_client.container_groups.list()

    # Get the container instances
    azure_instances = []
    for container_group in container_groups:
        group_expanded = container_client.container_groups.get(container_group.id.split("/")[4], container_group.name)
        
        azure_instance = {}
        azure_instance["id"] = container_group.id
        azure_instance["name"] = container_group.name
        azure_instance["image"] = container_group.containers[0].image
        
        if group_expanded.containers[0].instance_view is not None:
            azure_instance["status"] = group_expanded.containers[0].instance_view.current_state.state
        else:
            azure_instance["status"] = "Unknown"

        azure_instances.append(azure_instance)

    return azure_instances


def get_all_azure_repositories(credentials, subscription_id: str, registry_name: str, resource_group: str,
                               location: str):
    # Get acr url
    acr_url = get_acr_url(subscription_id, resource_group, registry_name, credentials, location)

    with ContainerRegistryClient(acr_url, credentials) as client:
        repositories = client.list_repository_names()

        repositories_response = []
        for repository in repositories:
            repostiory_response = {}
            repostiory_response["name"] = repository

            repositories_response.append(repostiory_response)

        return repositories_response


def delete_azure_repository(credentials, subscription_id: str, registry_name: str, resource_group: str,
                            repository_name: str, location: str):
    # Get acr url
    acr_url = get_acr_url(subscription_id, resource_group, registry_name, credentials, location)

    with ContainerRegistryClient(acr_url, credentials) as client:
        client.delete_repository(repository_name)


def delete_azure_container_instance(credentials, subscription_id: str, resource_group: str, instance_name: str):
    with ContainerInstanceManagementClient(credentials, subscription_id) as client:
        client.container_groups.begin_delete(resource_group, instance_name)


def get_subnet_id(credentials, subscription_id: str, resource_group: str, vnet_name: str,
                  subnet_name: str) -> str:
    # Get the subnet ID
    network_client = NetworkManagementClient(credentials, subscription_id)
    subnet = network_client.subnets.get(resource_group, vnet_name, subnet_name)

    return subnet.id


# create vnet and subnet if not exists
def associate_nsg_with_subnet(resource_group, vnet_name, subnet_name, nsg_name, subscription_id):
    # set default subscription
    cmd = f"az account set --subscription {subscription_id}"
    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Failed to set default subscription. Error: {result.stderr}")

    cmd = f"az network vnet subnet update --resource-group {resource_group} --vnet-name {vnet_name} --name {subnet_name} --network-security-group {nsg_name}"

    result = subprocess.run(cmd, capture_output=True, shell=True, text=True)

    if result.returncode != 0:
        raise Exception(f"Failed to associate nsg with subnet. Error: {result.stderr}")
    else:
        logger.info(f"Associated nsg '{nsg_name}' with subnet '{subnet_name}'.")


def create_vnet_and_subnet(credentials, subscription_id: str, resource_group: str, vnet_name: str,
                           location: str, subnet_name: str, nsg_name: str):
    # Create an Azure Network Management client
    network_client = NetworkManagementClient(credentials, subscription_id)

    # Check if the vnet exists
    vnet_exists = False
    vnets = network_client.virtual_networks.list(resource_group)
    for vnet in vnets:
        if vnet.name == vnet_name:
            vnet_exists = True
            break

    # Create the vnet if it does not exist
    if not vnet_exists:
        logger.info(f"Creating vnet '{vnet_name}' in resource group '{resource_group}'...")
        vnet_params = {"location": location, "address_space": {"address_prefixes": ["10.0.0.0/16"]}}
        async_vnet_creation = network_client.virtual_networks.begin_create_or_update(resource_group, vnet_name,
                                                                                     vnet_params)
        async_vnet_creation.wait()

    # Check if the subnet exists
    subnet_exists = False
    subnets = network_client.subnets.list(resource_group, vnet_name)
    for subnet in subnets:
        if subnet.name == subnet_name:
            subnet_exists = True
            break

    # Create the subnet if it does not exist
    if not subnet_exists:
        logger.info(f"Creating subnet '{subnet_name}' in resource group '{resource_group}'...")

        delegation = Delegation(name="ContainerInstance", service_name="Microsoft.ContainerInstance/containerGroups")

        subnet_params = {"address_prefix": "10.0.0.0/24", "delegations": [delegation]}
        async_subnet_creation = network_client.subnets.begin_create_or_update(resource_group, vnet_name, subnet_name,
                                                                              subnet_params)
        async_subnet_creation.wait()

    # Create the nsg if it does not exist
    nsg_exists = False
    nsgs = network_client.network_security_groups.list(resource_group)
    for nsg in nsgs:
        if nsg.name == nsg_name:
            nsg_exists = True
            break

    if not nsg_exists:
        logger.info(f"Creating nsg '{nsg_name}' in resource group '{resource_group}'...")
        nsg_params = {"location": location}
        async_nsg_creation = network_client.network_security_groups.begin_create_or_update(resource_group, nsg_name,
                                                                                           nsg_params)
        async_nsg_creation.wait()

        # associate nsg with subnet
        associate_nsg_with_subnet(resource_group, vnet_name, subnet_name, nsg_name, subscription_id)

    # Get the subnet ID
    subnet_id = get_subnet_id(credentials, subscription_id, resource_group, vnet_name, subnet_name)

    return subnet_id


def get_nsg_rules(credentials, subscription_id: str, resource_group: str, nsg_name: str):
    network_client = NetworkManagementClient(credentials, subscription_id)
    nsg = network_client.network_security_groups.get(resource_group, nsg_name)

    # combine default and custom rules
    security_rules = nsg.security_rules + nsg.default_security_rules

    output = []

    for rule in security_rules:
        security_rule = {}
        security_rule["id"] = rule.id
        security_rule["name"] = rule.name
        security_rule["priority"] = rule.priority
        security_rule["source_address_prefix"] = rule.source_address_prefix
        security_rule["source_port_range"] = rule.source_port_range
        security_rule["destination_address_prefix"] = rule.destination_address_prefix
        security_rule["destination_port_range"] = rule.destination_port_range
        security_rule["access"] = rule.access
        security_rule["protocol"] = rule.protocol
        security_rule["direction"] = rule.direction
        security_rule["description"] = rule.description
        security_rule["provisioning_state"] = rule.provisioning_state
        security_rule["access"] = rule.access

        output.append(security_rule)

    return output


def add_rule_to_nsg(credentials, subscription_id: str, resource_group: str, nsg_name: str,
                    rule_name: str, priority: int, direction: str,
                    source: str, source_port_range: str,
                    destination: str, destination_port_range: str,
                    access: str, protocol: str, description: str):
    network_client = NetworkManagementClient(credentials, subscription_id)
    nsg = network_client.network_security_groups.get(resource_group, nsg_name)

    # Add the rule to the NSG
    nsg.security_rules.append({
        "name": rule_name,
        "priority": priority,
        "direction": direction,
        "source_address_prefix": source,
        "source_port_range": source_port_range,
        "destination_address_prefix": destination,
        "destination_port_range": destination_port_range,
        "access": access,
        "protocol": protocol,
        "description": description
    })

    # Update the NSG
    network_client.network_security_groups.begin_create_or_update(resource_group, nsg_name, nsg)


def check_if_resource_group_exists(credentials, subscription_id, resource_group):
    resource_client = ResourceManagementClient(credentials, subscription_id)
    return resource_client.resource_groups.check_existence(resource_group)


def create_resource_group(credentials, subscription_id, resource_group, location):
    resource_client = ResourceManagementClient(credentials, subscription_id)
    resource_client.resource_groups.create_or_update(resource_group, {"location": location})


def get_container_instance_logs(credentials, subscription_id, resource_group, instance_name):
    container_client = ContainerInstanceManagementClient(credentials, subscription_id)
    logs = container_client.containers.list_logs(resource_group, instance_name, instance_name)

    # split the logs into a list of lines
    logs = logs.content.split("\n")

    return logs


def delete_nsg_rule(credentials, subscription_id, resource_group, nsg_name, rule_name):
    network_client = NetworkManagementClient(credentials, subscription_id)
    nsg = network_client.network_security_groups.get(resource_group, nsg_name)

    # Remove the rule from the NSG
    nsg.security_rules = [rule for rule in nsg.security_rules if rule.name != rule_name]

    # Update the NSG
    network_client.network_security_groups.begin_create_or_update(resource_group, nsg_name, nsg)
