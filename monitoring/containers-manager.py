import io
import time
import json
import logging
from typing import Callable
from functools import partial
from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import docker
import threading
from docker.models.containers import Container
import configparser
import os
import shutil
import tarfile

from monitoring.configuration import config_loader


# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("containers-manager")


def kafka_producer(message: str, topic: str, bootstrap_servers: str):
    producer = Producer({'bootstrap.servers': bootstrap_servers})
    producer.produce(topic, key='my_key', value=message)
    producer.flush()


def kafka_consumer(topic: str, group_id: str, callback: Callable[[str], None], bootstrap_servers: str):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    topic_metadata = admin_client.list_topics(timeout=5)
    if topic not in topic_metadata.topics:
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        admin_client.create_topics([new_topic])
        while topic not in admin_client.list_topics().topics:
            time.sleep(0.1)
    consumer.subscribe([topic])
    try:
        while True:
            messages = consumer.consume(10, timeout=1.0)
            for message in messages:
                if message is None:
                    continue
                if message.error():
                    if message.error().code() == KafkaError._PARTITION_EOF:
                        continue
                    else:
                        logger.error("Kafka error: %s", message.error().str())
                        continue
                logger.info("Received message on topic '%s': %s",
                            topic, message.value().decode())
                callback(message.value().decode())
    finally:
        consumer.close()



def prepare_docker_callback(callback: Callable[..., None], *args, **kwargs) -> Callable[[str], None]:
    return partial(callback, *args, **kwargs)


def create_docker_container(create_request: str, base_image_path: str):
    logger.info("Creating Docker container from file: %s", create_request)
    create_request = json.loads(create_request)
    file_id = create_request["fileId"]
    file_path = create_request["filePath"]
    container_name = create_request["containerName"]
    try:
        client = docker.from_env()
        new_image, _ = client.images.build(
            path=base_image_path, dockerfile="Dockerfile", tag=f"{container_name}_image")
        container = client.containers.run(new_image.id, detach=True, cap_add=[
                                          "NET_ADMIN"], network="mynetwork", name=container_name)
        container_path = f"/tmp/{file_id}"
        tarstream = io.BytesIO()
        with tarfile.open(fileobj=tarstream, mode='w') as tar:
            tar.add(file_path, arcname=file_id)
        tarstream.seek(0)
        container.put_archive(path='/tmp', data=tarstream)
        exec_command = ["bash", "-c",
                        f"chmod +x {container_path} && {container_path}"]
        exec_result = container.exec_run(cmd=exec_command, privileged=True)
        if exec_result.exit_code != 0:
            raise Exception("Failed to execute the file: %s" %
                            exec_result.output)
        logger.info("File executed inside the Docker container: %s", file_path)
    except docker.errors.APIError as e:
        logger.error("Failed to start Docker container: %s", e)


def delete_docker_container(container_id: str):
    logger.info("Deleting Docker container with ID: %s", container_id)
    try:
        client = docker.from_env()
        container = client.containers.get(container_id)
        container.stop()
        container.remove()
        logger.info(
            "Docker container with ID %s deleted successfully", container_id)
    except docker.errors.APIError as e:
        logger.error(
            "Failed to delete Docker container with ID %s: %s", container_id, e)


def list_containers_on_network(network_name: str) -> list[dict]:
    try:
        client = docker.from_env()
        containers = client.containers.list(filters={"network": network_name}, all=True)
        logger.info("Containers on the network '%s': %d", network_name, len(containers))
        containers_data = []
        for container in containers:
            containers_data.append({
                "id": container.id,
                "name": container.name,
                "status": container.status,
                "ip": container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"]
            })
        return containers_data
    except docker.errors.APIError as e:
        logger.error("Failed to list containers on the network: %s", e)


def monitor_containers_on_network(kafka_url: str, network_name: str, monitoring_interval: int):
    while True:
        containers_data = list_containers_on_network(network_name)
        kafka_producer(json.dumps(containers_data),
                       'containers-data', kafka_url)
        time.sleep(monitoring_interval)



def main():
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')
    base_image_path = config.get('docker', 'base_image_path')
    monitoring_interval = 5
    create_callback = prepare_docker_callback(
        create_docker_container, base_image_path=base_image_path)
    delete_callback = prepare_docker_callback(delete_docker_container)
    consumer_thread = threading.Thread(target=kafka_consumer, args=(
        'create-container', 'my-group-create-container', create_callback, kafka_url))
    consumer_thread.start()
    monitor_thread = threading.Thread(target=monitor_containers_on_network, args=(
        kafka_url, network_name, monitoring_interval))
    monitor_thread.start()
    delete_consumer_thread = threading.Thread(target=kafka_consumer, args=(
        'delete-container', 'my-group-delete-container', delete_callback, kafka_url))
    delete_consumer_thread.start()

    threads = [consumer_thread, monitor_thread, delete_consumer_thread]
    while True:
        for thread in threads:
            if not thread.is_alive():
                logger.error("Thread '%s' is not alive. Restarting...", thread.name)
                thread.start()
        time.sleep(1)



if __name__ == '__main__':
    main()
