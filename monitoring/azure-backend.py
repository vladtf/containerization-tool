import logging
import logging
import os
from time import sleep

from azure.core.exceptions import ResourceNotFoundError
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, ResourceRequirements,
                                                 ImageRegistryCredential)
from flask import Flask, request, jsonify
from flask_cors import CORS
from flask_mysqldb import MySQL

from azure_client import azure_client
from azure_client.azure_client import get_acr_access_token, get_subscription_id, AzureContainer, \
    get_acr_url, push_image_to_acr, get_azure_instance_data, get_all_azure_container_instances
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

        cursor = app.mysql.connection.cursor()

        # Check if the name is already in use
        query = f"SELECT * FROM azure_container WHERE name = '{container_data.name}'"
        cursor.execute(query)

        result = cursor.fetchall()

        if len(result) > 0:
            return f"Container with name {container_data.name} already exists", 400

        query = f"INSERT INTO azure_container (name, status, image) VALUES ('{container_data.name}', 'ready', '{container_data.image}')"
        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        return "Container pre-deployed successfully", 200
    except Exception as e:
        logger.error("Failed to pre-deploy container", e)
        return f"Failed to deploy container: {e}", 500


@app.route('/azure/repositories', methods=['GET'])
def get_all_azure_repositories():
    try:

        subscription_name = app.app_config.get("azure", "subscription_name")
        azure_repositories = azure_client.get_all_azure_repositories(
            credentials=app.azure_credentials,
            subscription_name=subscription_name,
            registry_name=app.app_config.get("azure", "acr_name"),
            resource_group=app.app_config.get("azure", "resource_group")
        )

        return jsonify(azure_repositories), 200

    except Exception as e:
        logger.error(f"Failed to get all registries: {e}")
        return f"Failed to get all registries: {e}", 500


@app.route('/azure/instances', methods=['GET'])
def get_all_azure_container_instances():
    try:
        azure_credentials = app.azure_credentials

        subscription_name = app.app_config.get("azure", "subscription_name")
        azure_instances = azure_client.get_all_azure_container_instances(app.azure_credentials, subscription_name)

        return jsonify(azure_instances), 200

    except Exception as e:
        logger.error(f"Failed to get all container instances: {e}")
        return f"Failed to get all container instances: {e}", 500


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
        container_data: AzureContainer = AzureContainer.from_dict(request.get_json())
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
        deploy_response = container_client.container_groups.begin_create_or_update(
            resource_group,
            container_group_name,
            container_group
        ).result()

        # Update the container status and azure container instance ID
        cursor = app.mysql.connection.cursor()

        query = (f"UPDATE azure_container "
                 f"SET status='deployed', instance_id='{deploy_response.id}', instance_name='{deploy_response.name}' "
                 f"WHERE name='{container_data.name}'")

        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        # For example, let's just return a success message for demonstration purposes
        return 'Container deployed successfully to Azure', 200

    except Exception as e:
        logger.error("An error occurred during deployment", e)
        return f'An error occurred during deployment: {e}', 500


@app.route('/azure/deploy/<container_id>', methods=['DELETE'])
def undeploy_from_azure(container_id):
    config = app.app_config

    subscription_name = config.get("azure", "subscription_name")
    resource_group = config.get("azure", "resource_group")

    try:
        logger.info(f"Starting undeployment of container {container_id}")

        # Get the container from the database
        cursor = app.mysql.connection.cursor()

        query = f"SELECT * FROM azure_container WHERE id={container_id}"
        cursor.execute(query)

        result = cursor.fetchone()

        azure_container = AzureContainer(*result)

        cursor.close()

        logger.info("Undeploying container: %s", container_id)
        credentials = DefaultAzureCredential()

        # Get the subscription ID
        subscription_id = get_subscription_id(subscription_name, credentials)
        if subscription_id is None:
            return f"Could not find a subscription with the name: {subscription_name}", 400

        # Get the container instance using the ID
        container_client = ContainerInstanceManagementClient(credentials, subscription_id)
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

        # Update the container status and azure container instance ID
        cursor = app.mysql.connection.cursor()

        query = (f"UPDATE azure_container "
                 f"SET status='ready', instance_id=NULL, instance_name=NULL "
                 f"WHERE id='{container_id}'")

        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        # For example, let's just return a success message for demonstration purposes
        return 'Container undeployed successfully from Azure', 200

    except ResourceNotFoundError as e:
        logger.error("Could not find the container instance", e)
        # update the container status and azure container instance ID
        cursor = app.mysql.connection.cursor()

        query = (f"UPDATE azure_container "
                 f"SET status='ready', instance_id=NULL, instance_name=NULL "
                 f"WHERE id='{container_id}'")

        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        return f"Could not find the container instance: {e}", 404
    except Exception as e:
        logger.error("An error occurred during undeployment", e)
        return f'An error occurred during undeployment: {e}', 500


@app.route('/azure/container/<container_id>', methods=['GET'])
def get_container(container_id):
    try:
        cursor = app.mysql.connection.cursor()

        query = f"SELECT * FROM azure_container WHERE id={container_id}"
        cursor.execute(query)

        result = cursor.fetchone()

        azure_container = AzureContainer(*result)

        cursor.close()

        azure_instance = get_azure_instance_data(azure_container, app.app_config)

        return jsonify(azure_instance), 200

    except Exception as e:
        logger.error(f"Failed to get container with id {container_id}: {e}")
        return f"Failed to get container with id {container_id}: {e}", 500


# listener to handle delete from database of 'ready' container
@app.route('/azure/container/<container_id>', methods=['DELETE'])
def delete_container(container_id):
    try:
        cursor = app.mysql.connection.cursor()

        query = f"DELETE FROM azure_container WHERE id={container_id}"

        cursor.execute(query)

        app.mysql.connection.commit()

        cursor.close()

        return f"Container with id {container_id} deleted successfully", 200

    except Exception as e:
        logger.error(f"Failed to delete container with id {container_id}: {e}")
        return f"Failed to delete container with id {container_id}: {e}", 500


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

    app.run(debug=True)
