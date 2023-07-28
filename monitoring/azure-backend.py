import json
import logging
import os

from flask import Flask, request
from flask_cors import CORS
from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, IpAddress, Port,
                                                 ResourceRequirements, ImageRegistryCredential)

from configuration import config_loader
from containers.docker_client import ContainerData

# Configure flask and CORS
app = Flask(__name__)
CORS(app)
app.logger.setLevel(logging.INFO)  # Set the desired logging level

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


@app.route('/azure/deploy', methods=['POST'])
def deploy_to_azure():
    config = app.app_config

    subscription_id = config.get("azure", "subscription_id")
    resource_group = config.get("azure", "resource_group")
    location = config.get("azure", "location")
    acr_server = config.get("azure", "acr_server")
    acr_username = config.get("azure", "acr_username")
    acr_password = config.get("azure", "acr_password")

    try:
        container_data: ContainerData = ContainerData.from_dict(request.get_json())
        logger.info(f"Starting deployment of container {container_data}")

        logger.info("Deploying container: %s", container_data)
        credential = DefaultAzureCredential()

        # Create a container instance
        container_group_name = "container-test-ping-sh"
        # container_image = f"{acr_server}/{container_data.image}:latest"
        container_image = f"{acr_server}/container-test-ping.sh_image:latest"

        # Configure the container properties
        container = Container(
            name="container-test-ping-sh",
            image=container_image,
            resources=ResourceRequirements(requests={"cpu": "1.0", "memoryInGB": "1.5"}),  # TODO: get from frontend
            ports=[ContainerPort(port=80)],
        )

        # Create ImageRegistryCredential object
        image_registry_credentials = [ImageRegistryCredential(
            server=acr_server,
            username=acr_username,
            password=acr_password
        )]

        # Configure the container group properties
        container_group = ContainerGroup(
            location=location,
            containers=[container],
            os_type="Linux",
            image_registry_credentials=image_registry_credentials
        )

        # Create the Azure Container Instance
        container_client = ContainerInstanceManagementClient(credential, subscription_id)
        container_client.container_groups.begin_create_or_update(resource_group, container_group_name,
                                                                 container_group).result()


        # For example, let's just return a success message for demonstration purposes
        response_data = {'message': 'Container deployed successfully to Azure'}
        return response_data, 200

    except Exception as e:
        logger.error("An error occurred during deployment", e)
        return f'An error occurred during deployment: {e}', 500


if __name__ == '__main__':
    # Load the configuration
    app_config = config_loader.load_config(os.path.abspath(__file__))

    app.app_config = app_config

    app.run(debug=True)
