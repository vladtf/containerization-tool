import json
import logging

import docker
import tarfile
import io

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


class DockerClientException(Exception):
    pass


class ContainerData:
    def __init__(self, id: str, name: str, status: str, ip: str):
        self.id = id
        self.name = name
        self.status = status
        self.ip = ip

    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'status': self.status,
            'ip': self.ip,
        }


def check_container_exists(container_id: str):
    client = docker.from_env()
    try:
        client.containers.get(container_id)
        return True
    except docker.errors.NotFound:
        return False


def create_docker_container(create_request: str, base_image_path: str, network_name: str):
    create_request = json.loads(create_request)
    file_id = create_request["fileId"]
    file_path = create_request["filePath"]
    container_name = create_request["containerName"].replace(" ", "_").lower()
    try:
        if check_container_exists(container_name):
            logger.info("Container '%s' already exists", container_name)
            return

        client = docker.from_env()
        new_image, _ = client.images.build(
            path=base_image_path, dockerfile="Dockerfile", tag=f"{container_name}_image")
        container = client.containers.run(new_image.id, detach=True, cap_add=[
            "NET_ADMIN"], network=network_name, name=container_name)
        container_path = f"/tmp/{file_id}"
        tarstream = io.BytesIO()
        with tarfile.open(fileobj=tarstream, mode='w') as tar:
            tar.add(file_path, arcname=file_id)
        tarstream.seek(0)
        container.put_archive(path='/tmp', data=tarstream)
        exec_command = ["bash", "-c",
                        f"chmod +x {container_path} && {container_path}"]
        container.exec_run(cmd=exec_command, detach=True, privileged=True)

    except Exception as e:
        raise DockerClientException("Failed to create Docker container: %s" % e)


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
                ip=container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"]
            ))
        return containers_data
    except Exception as e:
        raise DockerClientException(
            "Failed to list containers on the network: %s" % e)


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
            "Failed to delete Docker container with ID %s: %s" % (container_id, e))
