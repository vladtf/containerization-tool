import logging
import os
from time import sleep

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, ResourceRequirements,
                                                 ImageRegistryCredential, IpAddress, Port,
                                                 ContainerGroupNetworkProtocol, ContainerGroupIpAddressType,
                                                 ContainerGroupSubnetId)
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

import mysql_client.mysql_client
from azure_client import azure_client
from azure_client.azure_client import get_acr_access_token, get_subscription_id, AzureContainer, \
    get_acr_url, push_image_to_acr, get_azure_instance_data
from configuration import config_loader
from containers.docker_client import ContainerData

# Configure flask and CORS
app = Flask(__name__)
CORS(app)  # TODO: be more restrictive
app.logger.setLevel(logging.INFO)  # Set the desired logging level

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Disable the Azure SDK logging for HTTP requests
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)


@app.route('/azure/pre-deploy', methods=['POST'])
def pre_deploy_to_azure():
    try:
        container_data: ContainerData = ContainerData.from_dict(request.get_json())
        logger.info(f"Starting pre-deployment of container {container_data}")

        # Check if the name is already in use
        if mysql_client.mysql_client.azure_container_exists_by_name(mysql=app.mysql,
                                                                    container_name=container_data.name):
            return f"Container with name {container_data.name} already exists", 400

        azure_container = AzureContainer(
            name=container_data.name,
            status="ready",
            image=container_data.image,
            instance_id="",
            instance_name="",
            id=-1
        )

        mysql_client.mysql_client.insert_azure_container(mysql=app.mysql, azure_container=azure_container)

        return "Container pre-deployed successfully", 200
    except Exception as e:
        logger.error("Failed to pre-deploy container", e)
        return f"Failed to deploy container: {e}", 500


@app.route('/azure/repositories', methods=['GET'])
def get_all_azure_repositories():
    try:
        azure_repositories = azure_client.get_all_azure_repositories(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            registry_name=app.app_config.get("azure", "acr_name"),
            resource_group=app.app_config.get("azure", "resource_group")
        )

        return jsonify(azure_repositories), 200

    except Exception as e:
        logger.error(f"Failed to get all registries", e)
        return f"Failed to get all registries: {e}", 500


@app.route('/azure/instances', methods=['GET'])
def get_all_azure_container_instances():
    try:
        azure_credentials = app.azure_credentials

        azure_instances = azure_client.get_all_azure_container_instances(
            credentials=azure_credentials,
            subscription_id=app.azure_subscription_id)

        return jsonify(azure_instances), 200

    except Exception as e:
        logger.error(f"Failed to get all container instances", e)
        return f"Failed to get all container instances: {e}", 500


@app.route('/azure/all', methods=['GET'])
def get_all_azure_container():
    try:
        azure_containers = mysql_client.mysql_client.get_all_azure_containers(
            mysql=app.mysql,
        )

        return jsonify([container.to_dict() for container in azure_containers]), 200

    except Exception as e:
        logger.error(f"Failed to get all container", e)
        return f"Failed to get all container: {e}", 500


@app.route('/azure/deploy', methods=['POST'])
def deploy_to_azure():
    config = app.app_config

    resource_group = config.get("azure", "resource_group")
    location = config.get("azure", "location")
    acr_name = config.get("azure", "acr_name")

    try:
        container_data: AzureContainer = AzureContainer.from_dict(request.get_json())
        logger.info(f"Starting deployment of container {container_data}")

        logger.info("Deploying container: %s", container_data)

        # Get the ACR URL
        acr_url = get_acr_url(app.azure_subscription_id, resource_group, acr_name, app.azure_credentials)
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
            ports=[ContainerPort(port=8080)],
        )

        # Create ImageRegistryCredential object
        image_registry_credentials = [ImageRegistryCredential(
            server=acr_url,
            username="00000000-0000-0000-0000-000000000000",
            password=get_acr_access_token(acr_url)
        )]

        # Configure IP address
        # ip_address = IpAddress(
        #     ports=[Port(protocol=ContainerGroupNetworkProtocol.tcp, port=8080)],
        #     type=ContainerGroupIpAddressType.public
        # )

        # Configure subnet
        subnet_id = azure_client.get_subnet_id(
            credentials=app.azure_credentials,
            resource_group=resource_group,
            vnet_name=config.get("azure", "vnet_name"),
            subnet_name=config.get("azure", "subnet_name"),
            subscription_id=app.azure_subscription_id
        )

        subnet = ContainerGroupSubnetId(
            name=config.get("azure", "subnet_name"),
            id=subnet_id)

        # Configure the container group properties
        container_group = ContainerGroup(
            location=location,
            containers=[container],
            os_type="Linux",
            image_registry_credentials=image_registry_credentials,
            # ip_address=ip_address,
            subnet_ids=[subnet]
        )

        # Create the Azure Container Instance
        container_client = ContainerInstanceManagementClient(credentials, subscription_id)
        deploy_response = container_client.container_groups.begin_create_or_update(
            resource_group,
            container_group_name,
            container_group
        ).result()

        azure_container = mysql_client.mysql_client.get_azure_container_by_name(
            mysql=app.mysql,
            container_name=container_data.name)

        azure_container.status = "deployed"
        azure_container.instance_id = deploy_response.id
        azure_container.instance_name = deploy_response.name

        mysql_client.mysql_client.update_azure_container(mysql=app.mysql, azure_container=azure_container)

        # For example, let's just return a success message for demonstration purposes
        return 'Container deployed successfully to Azure', 200

    except Exception as e:
        logger.error("An error occurred during deployment", e)
        return f'An error occurred during deployment: {e}', 500


@app.route('/azure/deploy/<container_id>', methods=['DELETE'])
def undeploy_from_azure(container_id):
    config = app.app_config

    resource_group = config.get("azure", "resource_group")

    try:
        logger.info(f"Starting undeployment of container {container_id}")

        azure_container = mysql_client.mysql_client.get_azure_container_by_id(
            mysql=app.mysql,
            container_id=container_id
        )

        logger.info("Undeploying container: %s", container_id)

        # Get the container instance using the ID
        container_client = ContainerInstanceManagementClient(
            credential=app.azure_credentials,
            subscription_id=app.azure_subscription_id
        )

        container_group = container_client.container_groups.get(resource_group, azure_container.instance_name)

        # Delete the container instance
        response = container_client.container_groups.begin_delete(resource_group,
                                                                  azure_container.instance_name).result()

        # Wait for the container to be deleted
        try:
            while container_group.containers[0].instance_view.current_state.state != "Terminated":
                container_group = container_client.container_groups.get(resource_group, azure_container.instance_name)
                sleep(1)
        except Exception as e:  # TODO: to properly check the deletion status
            logger.error("An error occurred while waiting for the container to be deleted", e)

        # TODO: check if the container was deleted successfully

        # TODO: delete image from ACR

        azure_container = mysql_client.mysql_client.get_azure_container_by_id(
            mysql=app.mysql,
            container_id=container_id
        )

        azure_container.status = "ready"
        azure_container.instance_id = None
        azure_container.instance_name = None

        mysql_client.mysql_client.update_azure_container(mysql=app.mysql, azure_container=azure_container)

        # For example, let's just return a success message for demonstration purposes
        return 'Container undeployed successfully from Azure', 200

    except ResourceNotFoundError as e:
        logger.error("Could not find the container instance", e)

        azure_container = mysql_client.mysql_client.get_azure_container_by_id(
            mysql=app.mysql,
            container_id=container_id
        )

        azure_container.status = "ready"
        azure_container.instance_id = None
        azure_container.instance_name = None

        mysql_client.mysql_client.update_azure_container(mysql=app.mysql, azure_container=azure_container)

        return f"Could not find the container instance: {e}", 404
    except Exception as e:
        logger.error("An error occurred during undeployment", e)
        return f'An error occurred during undeployment: {e}', 500


@app.route('/azure/container/<container_name>', methods=['GET'])
def get_container(container_name):
    try:
        azure_container = mysql_client.mysql_client.get_azure_container_by_name(
            mysql=app.mysql,
            container_name=container_name
        )

        # if the container is not deployed yet, return the container data from the database
        if azure_container.status != "deployed":
            return jsonify(azure_container), 200

        azure_instance = get_azure_instance_data(
            credentials=app.azure_credentials,
            resource_group=app.app_config.get("azure", "resource_group"),
            azure_container=azure_container,
            subscription_id=app.azure_subscription_id
        )

        return jsonify(azure_instance), 200

    except Exception as e:
        logger.error(f"Failed to get container with name {container_name}", e)
        return f"Failed to get container with name {container_name}: {e}", 500


# listener to handle delete from database of 'ready' container
@app.route('/azure/container/<container_id>', methods=['DELETE'])
def delete_container(container_id):
    try:
        mysql_client.mysql_client.delete_azure_container_by_id(
            mysql=app.mysql,
            container_id=container_id
        )

        return f"Container with id {container_id} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete container with id {container_id}", e)
        return f"Failed to delete container with id {container_id}: {e}", 500


# listener to handle delete of a repository from ACR
@app.route('/azure/repository/<repository_name>', methods=['DELETE'])
def delete_repository(repository_name):
    try:
        config = app.app_config
        resource_group = config.get("azure", "resource_group")
        acr_name = config.get("azure", "acr_name")

        azure_client.delete_azure_repository(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            registry_name=acr_name,
            resource_group=resource_group,
            repository_name=repository_name
        )

        return f"Repository with name {repository_name} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete repository with name {repository_name}", e)
        return f"Failed to delete repository with name {repository_name}: {e}", 500


# listener to handle delete of container instance from Azure
@app.route('/azure/instances/<instance_name>', methods=['DELETE'])
def delete_azure_instance(instance_name):
    try:

        azure_client.delete_azure_container_instance(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            resource_group=app.app_config.get("azure", "resource_group"),
            instance_name=instance_name
        )

        return f"Container instance with name {instance_name} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete container instance with name {instance_name}", e)
        return f"Failed to delete container instance with name {instance_name}: {e}", 500


# listener to get all the nsg rules
@app.route('/azure/security-rules', methods=['GET'])
def get_nsg_rules():
    try:
        nsg_rules = azure_client.get_nsg_rules(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            resource_group=app.app_config.get("azure", "resource_group"),
            nsg_name=app.app_config.get("azure", "nsg_name")
        )

        return jsonify(nsg_rules), 200

    except Exception as e:
        logger.error(f"Failed to get nsg rules", e)
        return f"Failed to get nsg rules: {e}", 500


# listener to add a nsg rule
@app.route('/azure/security-rules', methods=['POST'])
def add_nsg_rule():
    try:
        data = request.get_json()

        nsg_rule = azure_client.add_rule_to_nsg(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            resource_group=app.app_config.get("azure", "resource_group"),
            nsg_name=app.app_config.get("azure", "nsg_name"),
            rule_name=data.get("name"),
            access=data.get("access"),
            source=data.get("source"),
            priority=data.get("priority"),
            protocol=data.get("protocol"),
            direction=data.get("direction"),
            description=data.get("description"),
            destination=data.get("destination"),
            source_port_range=data.get("sourcePortRange"),
            destination_port_range=data.get("destinationPortRange")
        )

        return jsonify(nsg_rule), 200

    except Exception as e:
        logger.error(f"Failed to add nsg rule", e)
        return f"Failed to add nsg rule: {e}", 500


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

    # Init Azure Credentials
    credentials = DefaultAzureCredential()
    app.azure_credentials = credentials

    # Get Azure Subscription ID
    subscription_name = app_config.get("azure", "subscription_name")
    subscription_id = get_subscription_id(subscription_name, credentials)
    if subscription_id is None:
        raise Exception(f"Could not find a subscription with the name: {subscription_name}")
    app.azure_subscription_id = subscription_id

    app.run(debug=True)
