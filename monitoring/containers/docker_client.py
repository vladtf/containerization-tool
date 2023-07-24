import io
import json
import logging
import os
import shutil
from dataclasses import dataclass, asdict

import docker

from kafka.kafka_client import DataClassEncoder

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class DockerClientException(Exception):
    pass


@dataclass
class ContainerData:
    id: str
    name: str
    status: str
    ip: str
    image: str
    created: str

    def to_dict(self):
        return asdict(self)

    def to_json(self):
        return json.dumps(self.to_dict(), cls=DataClassEncoder)


def check_container_exists(container_id: str):
    client = docker.from_env()
    try:
        client.containers.get(container_id)
        return True
    except docker.errors.NotFound:
        return False


def get_dockerfile_by_type(file_type: str):
    file_type = file_type.lower()

    dockerfile_map = {
        "python": "Dockerfile.python",
        "jar": "Dockerfile.java",
        "c": "Dockerfile.c",
        "javascript": "Dockerfile.javascript",
        "default": "Dockerfile.default"
    }

    return dockerfile_map.get(file_type, dockerfile_map["default"])


def create_docker_container(create_request: dict,
                            base_image_path: str, network_name: str,
                            fluentd_address: str, fluentd_format: str, fluentd_driver: str):
    file_id = create_request["fileId"]
    file_path = create_request["filePath"]
    container_name = create_request["containerName"]
    file_type = create_request["fileType"]

    try:
        if check_container_exists(container_name):
            raise DockerClientException(
                f"Container with name '{container_name}' already exists")

        # Copy the file to the base image path
        shutil.copy(file_path, os.path.join(base_image_path, "entrypoint.bin"))

        # Build the new image
        client = docker.from_env()

        docker_file = get_dockerfile_by_type(file_type)
        logger.info("Using Dockerfile '%s' to create container '%s'",
                    docker_file, container_name)

        # Build the base image
        base_image, _ = client.images.build(
            path=base_image_path, dockerfile="Dockerfile.base", tag=f"containerization-tool-base-image", rm=True)

        # Check if the base image was built successfully
        if base_image is None:
            raise DockerClientException("Failed to build base image for container")

        # Build the new image
        new_image, _ = client.images.build(
            path=base_image_path, dockerfile=docker_file, tag=f"{container_name}_image", rm=True)

        # Check if the new image was built successfully
        if new_image is None:
            raise DockerClientException("Failed to build new image for container")

        log_config = {
            'type': fluentd_driver,
            'config': {
                'syslog-format': fluentd_format,
                'syslog-address': fluentd_address
            }
        }

        container = client.containers.run(
            new_image.id,
            detach=True,
            cap_add=["NET_ADMIN"],
            network=network_name,
            name=container_name,
            log_config=log_config
        )

    except Exception as e:
        raise DockerClientException(
            f"Failed to create Docker container with name {container_name}: {e}")


def list_containers_on_network(network_name: str) -> list[ContainerData]:
    try:
        client = docker.from_env()
        containers = client.containers.list(
            filters={"network": network_name}, all=True)
        containers_data = []
        for container in containers:
            containers_data.append(ContainerData(
                id=container.id,
                name=container.name,
                status=container.status,
                ip=container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"],
                created=container.attrs["Created"],
                image=container.attrs["Config"]["Image"]
            ))
        return containers_data
    except Exception as e:
        raise DockerClientException(f"Failed to list containers: {e}")


def delete_docker_container(container_id: str):
    try:
        if not check_container_exists(container_id):
            logger.info("Container '%s' does not exist", container_id)
            return

        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
        container.remove()
    except Exception as e:
        raise DockerClientException(
            f"Failed to delete container {container_id}: {e}")
