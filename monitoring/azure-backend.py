import logging
import os
from time import sleep

import docker
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

import containers.docker_client
import mysql_client.mysql_client
from azure_client import azure_client
from azure_client.azure_client import get_acr_access_token, get_subscription_id, AzureContainer, \
    get_acr_url, push_image_to_acr, get_azure_instance_data
from configuration import config_loader
from containers.docker_client import ContainerData

# Configure flask and CORS
app = Flask(__name__)

# Load the configuration
app_config = config_loader.load_config(os.path.abspath(__file__))
app.app_config = app_config

app.config['MYSQL_HOST'] = os.environ.get("MYSQL_HOST") or app_config.get("mysql", "host")
app.config['MYSQL_USER'] = os.environ.get("MYSQL_USER") or app_config.get("mysql", "user")
app.config['MYSQL_PASSWORD'] = os.environ.get("MYSQL_PASSWORD") or app_config.get("mysql", "password")
app.config['MYSQL_DB'] = os.environ.get("MYSQL_DB") or app_config.get("mysql", "database")

# Init Azure Credentials
credentials = DefaultAzureCredential()
app.azure_credentials = credentials

# Init MySQL
mysql = MySQL(app)
app.mysql = mysql

CORS(app, resources={r"/*": {"origins": "http://localhost:3000"}})
app.logger.setLevel(logging.INFO)  # Set the desired logging level

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Disable the Azure SDK logging for HTTP requests
azure_logger = logging.getLogger('azure')
azure_logger.setLevel(logging.WARNING)


# Get Azure Subscription ID
subscription_name = os.environ.get(
    "AZURE_SUBSCRIPTION_NAME") or app_config.get("azure", "subscription_name")
subscription_id = azure_client.get_subscription_id(subscription_name, credentials)
if subscription_id is None:
    # list all subscriptions
    subscriptions = azure_client.get_all_subscriptions(credentials)
    logger.error(
        f"Could not find a subscription with the name: {subscription_name}. Please run again generation of the service principal and make sure the subscription name is correct and you provided the right credentials.")
    
    raise Exception(f"Could not find a subscription with the name: {subscription_name}")

app.azure_subscription_id = subscription_id
    


@app.route('/azure/pre-deploy', methods=['POST'])
def pre_deploy_to_azure():
    try:
        container_data: ContainerData = ContainerData.from_dict(
            request.get_json())
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

        mysql_client.mysql_client.insert_azure_container(
            mysql=app.mysql, azure_container=azure_container)

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
            resource_group=app.app_config.get("azure", "resource_group"),
            location=app.app_config.get("azure", "location"),
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
        container_data: AzureContainer = AzureContainer.from_dict(
            request.get_json())
        logger.info(f"Starting deployment of container {container_data}")

        logger.info("Deploying container: %s", container_data)

        # Get the ACR URL
        acr_url = get_acr_url(app.azure_subscription_id, resource_group,
                              acr_name, app.azure_credentials, location)
        if acr_url is None:
            return f"Could not find an Azure Container Registry with the name: {acr_name}", 400

        # Push the image to the ACR
        logger.info("Pushing image to ACR")
        acr_image_name = push_image_to_acr(container_data, acr_url)

        # Configure the container properties
        container_group_name = container_data.name
        container = Container(
            name=container_group_name,
            image=acr_image_name,
            resources=ResourceRequirements(
                requests={"cpu": "1.0", "memoryInGB": "1.5"}),  # TODO: get from frontend
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

        # Create vnet if it doesn't exist
        logger.info("Checking network configuration")
        azure_client.create_vnet_and_subnet(
            credentials=app.azure_credentials,
            vnet_name=config.get("azure", "vnet_name"),
            subscription_id=app.azure_subscription_id,
            subnet_name=config.get("azure", "subnet_name"),
            resource_group=resource_group,
            location=location,
            nsg_name=config.get("azure", "nsg_name"),
        )

        # Configure subnet
        logger.info("Getting subnet ID")
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
        logger.info("Creating container instance")
        container_client = ContainerInstanceManagementClient(
            credentials, subscription_id)
        deploy_response = container_client.container_groups.begin_create_or_update(
            resource_group,
            container_group_name,
            container_group
        ).result()

        # Getting the container instance data
        logger.info("Getting container instance data")
        azure_container = mysql_client.mysql_client.get_azure_container_by_name(
            mysql=app.mysql,
            container_name=container_data.name)

        azure_container.status = "deployed"
        azure_container.instance_id = deploy_response.id
        azure_container.instance_name = deploy_response.name

        # Update the container instance data in the database
        logger.info("Updating container instance data in the database")
        mysql_client.mysql_client.update_azure_container(
            mysql=app.mysql, azure_container=azure_container)

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

        container_group = container_client.container_groups.get(
            resource_group, azure_container.instance_name)

        # Delete the container instance
        response = container_client.container_groups.begin_delete(resource_group,
                                                                  azure_container.instance_name).result()

        # Wait for the container to be deleted
        try:
            while container_group.containers[0].instance_view.current_state.state != "Terminated":
                container_group = container_client.container_groups.get(
                    resource_group, azure_container.instance_name)
                sleep(1)
        except Exception as e:  # TODO: to properly check the deletion status
            logger.error(
                "An error occurred while waiting for the container to be deleted", e)

        # TODO: check if the container was deleted successfully

        # TODO: delete image from ACR

        azure_container = mysql_client.mysql_client.get_azure_container_by_id(
            mysql=app.mysql,
            container_id=container_id
        )

        azure_container.status = "ready"
        azure_container.instance_id = None
        azure_container.instance_name = None

        mysql_client.mysql_client.update_azure_container(
            mysql=app.mysql, azure_container=azure_container)

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

        mysql_client.mysql_client.update_azure_container(
            mysql=app.mysql, azure_container=azure_container)

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
        logger.error(
            f"Failed to delete repository with name {repository_name}", e)
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
        logger.error(
            f"Failed to delete container instance with name {instance_name}", e)
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


# route to get container instance logs
@app.route('/azure/logs/<instance_name>', methods=['GET'])
def get_container_instance_logs(instance_name):
    try:
        logs = azure_client.get_container_instance_logs(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            resource_group=app.app_config.get("azure", "resource_group"),
            instance_name=instance_name
        )

        return jsonify(logs), 200

    except Exception as e:
        logger.error(f"Failed to get container instance logs", e)
        return f"Failed to get container instance logs: {e}", 500


# route to delete nsg rule by name
@app.route('/azure/security-rules/<rule_name>', methods=['DELETE'])
def delete_nsg_rule(rule_name):
    try:
        azure_client.delete_nsg_rule(
            credentials=app.azure_credentials,
            subscription_id=app.azure_subscription_id,
            resource_group=app.app_config.get("azure", "resource_group"),
            nsg_name=app.app_config.get("azure", "nsg_name"),
            rule_name=rule_name
        )

        return f"Rule with name {rule_name} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete rule with name {rule_name}", e)
        return f"Failed to delete rule with name {rule_name}: {e}", 500


# route to delete docker container by id
@app.route('/docker/<container_id>', methods=['DELETE'])
def delete_docker_container(container_id):
    try:
        containers.docker_client.delete_docker_container(container_id)
        return f"Container with id {container_id} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete container with id {container_id}", e)
        return f"Failed to delete container with id {container_id}: {e}", 500


# route to list all docker containers
@app.route('/docker', methods=['GET'])
def list_docker_containers():
    try:
        network_name = app.app_config.get("docker", "network_name")
        containers_data = containers.docker_client.list_containers_on_network(
            network_name=network_name
        )
        return jsonify([container.to_dict() for container in containers_data]), 200

    except Exception as e:
        logger.error(f"Failed to list docker containers", e)
        return f"Failed to list docker containers: {e}", 500

# route to restart a container


@app.route('/docker/<container_id>/restart', methods=['POST'])
def restart_docker_container(container_id):
    try:
        containers.docker_client.restart_docker_container(container_id)
        return f"Container with id {container_id} restarted successfully", 200

    except Exception as e:
        logger.error(f"Failed to restart container with id {container_id}", e)
        return f"Failed to restart container with id {container_id}: {e}", 500


if __name__ == '__main__':
    # Check if the resource group exists, if not create it
    resource_group = app_config.get("azure", "resource_group")
    if not azure_client.check_if_resource_group_exists(credentials, subscription_id, resource_group):
        logger.info(f"Creating resource group {resource_group}")
        azure_client.create_resource_group(credentials, subscription_id, resource_group,
                                           app_config.get("azure", "location"))
    
    tenant_id = os.environ.get("AZURE_TENANT_ID")
    client_id = os.environ.get("AZURE_CLIENT_ID")
    client_secret = os.environ.get("AZURE_CLIENT_SECRET")
    
    if tenant_id is None or client_id is None or client_secret is None:
        logger.error("Please provide the Azure credentials as environment variables")
        raise Exception("Please provide the Azure credentials as environment variables")
    
    azure_client.login_to_azure_as_service_principal(tenant_id, client_id, client_secret)

    logger.info("Starting Flask server")
    app.run(host='0.0.0.0', port=5000, debug=True)
            
