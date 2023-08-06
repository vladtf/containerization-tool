import configparser
import json
import logging
import subprocess
from dataclasses import dataclass, asdict

import docker
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.subscription import SubscriptionClient
from azure.containerregistry import ContainerRegistryClient

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


def get_acr_url(subscription_id, resource_group, acr_server, credentials):
    acr_client = ContainerRegistryManagementClient(credentials, subscription_id)

    try:
        acr = acr_client.registries.get(resource_group, acr_server)
        logger.info(f"Container registry '{acr_server}' exists in the Azure subscription.")
        return acr.login_server
    except ResourceNotFoundError:
        logger.warning(f"Container registry '{acr_server}' not found in the Azure subscription.")
        return None


def get_azure_instance_data(azure_container: AzureContainer, config: configparser.ConfigParser):
    subscription_name = config.get("azure", "subscription_name")
    resource_group = config.get("azure", "resource_group")

    azure_instance = azure_container.to_dict()

    credentials = DefaultAzureCredential()

    # Get the subscription ID
    subscription_id = get_subscription_id(subscription_name, credentials)
    if subscription_id is None:
        raise Exception(f"Could not find a subscription with the name: {subscription_name}")

    # Get the container instance using the ID
    container_client = ContainerInstanceManagementClient(credentials, subscription_id)
    container_group = container_client.container_groups.get(resource_group, azure_container.name)

    azure_instance["instance_id"] = container_group.id
    azure_instance["instance_name"] = container_group.name
    azure_instance["instance_status"] = container_group.containers[0].instance_view.current_state.state
    # azure_instance["instance_ip"] = container_group.ip_address.ip # TODO: get IP address
    azure_instance["instance_ports"] = [port.port for port in container_group.containers[0].ports]
    azure_instance["instance_image"] = container_group.containers[0].image
    azure_instance["instance_start_time"] = container_group.containers[0].instance_view.current_state.start_time

    return azure_instance


def get_all_azure_container_instances(credentials, subscription_name: str) -> list:
    # Get the subscription ID
    subscription_id = get_subscription_id(subscription_name, credentials)
    if subscription_id is None:
        raise Exception(f"Could not find a subscription with the name: {subscription_name}")

    # Get the container instances
    container_client = ContainerInstanceManagementClient(credentials, subscription_id)
    container_groups = container_client.container_groups.list()

    # Get the container instances
    azure_instances = []
    for container_group in container_groups:
        azure_instance = {}
        azure_instance["id"] = container_group.id
        azure_instance["name"] = container_group.name
        azure_instance["image"] = container_group.containers[0].image

        azure_instances.append(azure_instance)

    return azure_instances


def get_all_azure_repositories(credentials, subscription_name: str, registry_name: str, resource_group: str) -> list:
    # Get the subscription ID
    subscription_id = get_subscription_id(subscription_name, credentials)
    if subscription_id is None:
        raise Exception(f"Could not find a subscription with the name: {subscription_name}")

    # Get acr url
    acr_url = get_acr_url(subscription_id, resource_group, registry_name, credentials)

    with ContainerRegistryClient(acr_url, credentials) as client:
        repositories = client.list_repository_names()

        repositories_response = []
        for repository in repositories:
            repostiory_response = {}
            repostiory_response["name"] = repository

            repositories_response.append(repostiory_response)

        return repositories_response


def delete_azure_repository(credentials, subscription_id: str, registry_name: str, resource_group: str,
                            repository_name: str):
    # Get acr url
    acr_url = get_acr_url(subscription_id, resource_group, registry_name, credentials)

    with ContainerRegistryClient(acr_url, credentials) as client:
        client.delete_repository(repository_name)


def delete_azure_container_instance(credentials, subscription_id: str, resource_group: str, instance_name: str):
    with ContainerInstanceManagementClient(credentials, subscription_id) as client:
        client.container_groups.begin_delete(resource_group, instance_name)