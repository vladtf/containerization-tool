import json
import logging
import os
import subprocess
from dataclasses import dataclass, asdict

import docker
from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, ResourceRequirements,
                                                 ImageRegistryCredential)
from azure.mgmt.containerregistry import ContainerRegistryManagementClient
from azure.mgmt.subscription import SubscriptionClient
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

from configuration import config_loader
from containers.docker_client import ContainerData
from kafka.kafka_client import DataClassEncoder

# Configure flask and CORS
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)  # Set the desired logging level

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


@dataclass
class AzureContainer:
    id: int
    name: str
    status: str
    image: str

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DataClassEncoder)

    @classmethod
    def from_dict(cls, param):
        return cls(**param)


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


def login_to_acr(acr_url):
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


def push_image_to_acr(container_data: ContainerData, acr_url):
    # Login to the ACR
    docker_client = login_to_acr(acr_url)

    # Check if the image exists locally
    image = docker_client.images.get(container_data.image)
    logger.info(f"Image {container_data.image} found locally.")

    # Tag the image with the ACR URL
    acr_image_name = f"{acr_url}/{container_data.image}:latest"
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


@app.route('/azure/pre-deploy', methods=['POST'])
def pre_deploy_to_azure():
    config = app.app_config

    try:
        container_data: ContainerData = ContainerData.from_dict(request.get_json())
        logger.info(f"Starting pre-deployment of container {container_data}")

        cursor = app.mysql.connection.cursor()

        query = f"INSERT INTO azure_container (name, status, image) VALUES ('{container_data.name}', 'ready', '{container_data.image}')"
        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        return "Container pre-deployed successfully", 200
    except Exception as e:
        logger.error("Failed to pre-deploy container", e)
        return f"Failed to deploy container: {e}", 500


@app.route('/azure/all', methods=['GET'])
def get_all_azure_container():
    try:
        cursor = app.mysql.connection.cursor()

        query = f"SELECT * FROM azure_container"
        cursor.execute(query)

        result = cursor.fetchall()

        azure_containers = [AzureContainer(*row) for row in result]

        cursor.close()

        return jsonify([container.to_dict() for container in azure_containers]), 200

    except Exception as e:
        logger.error(f"Failed to get all container: {e}")
        return f"Failed to get all container: {e}", 500


@app.route('/azure/deploy', methods=['POST'])
def deploy_to_azure():
    config = app.app_config

    subscription_name = config.get("azure", "subscription_name")
    resource_group = config.get("azure", "resource_group")
    location = config.get("azure", "location")
    acr_name = config.get("azure", "acr_name")

    try:
        container_data: ContainerData = ContainerData.from_dict(request.get_json())
        logger.info(f"Starting deployment of container {container_data}")

        logger.info("Deploying container: %s", container_data)
        credentials = DefaultAzureCredential()

        # Get the subscription ID
        subscription_id = get_subscription_id(subscription_name, credentials)
        if subscription_id is None:
            return f"Could not find a subscription with the name: {subscription_name}", 400

        # Get the ACR URL
        acr_url = get_acr_url(subscription_id, resource_group, acr_name, credentials)
        if acr_url is None:
            return f"Could not find an Azure Container Registry with the name: {acr_name}", 400

        # Push the image to the ACR
        acr_image_name = push_image_to_acr(container_data, acr_url)

        # Configure the container properties
        container_group_name = container_data.name
        container = Container(
            name=container_group_name,
            image=acr_image_name,
            resources=ResourceRequirements(requests={"cpu": "1.0", "memoryInGB": "1.5"}),  # TODO: get from frontend
            ports=[ContainerPort(port=80)],
        )

        # Create ImageRegistryCredential object
        image_registry_credentials = [ImageRegistryCredential(
            server=acr_url,
            username="00000000-0000-0000-0000-000000000000",
            password=get_acr_access_token(acr_url)
        )]

        # Configure the container group properties
        container_group = ContainerGroup(
            location=location,
            containers=[container],
            os_type="Linux",
            image_registry_credentials=image_registry_credentials
        )

        # Create the Azure Container Instance
        container_client = ContainerInstanceManagementClient(credentials, subscription_id)
        container_client.container_groups.begin_create_or_update(resource_group, container_group_name,
                                                                 container_group).result()

        # For example, let's just return a success message for demonstration purposes
        return 'Container deployed successfully to Azure', 200

    except Exception as e:
        logger.error("An error occurred during deployment", e)
        return f'An error occurred during deployment: {e}', 500


@app.route('/azure/get', methods=['GET'])
def get_all_containers():
    config = app.app_config

    subscription_name = config.get("azure", "subscription_name")
    resource_group = config.get("azure", "resource_group")
    location = config.get("azure", "location")
    acr_name = config.get("azure", "acr_name")

    try:
        credentials = DefaultAzureCredential()

        # Get the subscription ID
        subscription_id = get_subscription_id(subscription_name, credentials)
        if subscription_id is None:
            return f"Could not find a subscription with the name: {subscription_name}", 400

        # Get the ACR URL
        acr_url = get_acr_url(subscription_id, resource_group, acr_name, credentials)
        if acr_url is None:
            return f"Could not find an Azure Container Registry with the name: {acr_name}", 400

        # Login to the ACR
        docker_client = login_to_acr(acr_url)

        # Get all the images from the ACR
        images = docker_client.images.list()

        # Return the images
        return json.dumps([image.tags[0] for image in images]), 200

    except Exception as e:
        logger.error("An error occurred while getting images", e)
        return f'An error occurred while getting images: {e}', 500


if __name__ == '__main__':
    # Load the configuration
    app_config = config_loader.load_config(os.path.abspath(__file__))

    app.app_config = app_config

    app.config['MYSQL_HOST'] = app_config.get("mysql", "host")
    app.config['MYSQL_USER'] = app_config.get("mysql", "user")
    app.config['MYSQL_PASSWORD'] = app_config.get("mysql", "password")
    app.config['MYSQL_DB'] = app_config.get("mysql", "database")

    mysql = MySQL(app)
    app.mysql = mysql

    app.run(debug=True)
