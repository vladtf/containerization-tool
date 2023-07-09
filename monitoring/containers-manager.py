import time
import json
import logging
from confluent_kafka import Producer, Consumer, KafkaError
import docker
import threading
from confluent_kafka.admin import AdminClient, NewTopic
import configparser
import os

# Configure the logger
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def load_config():
    # Get the directory path of the script
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to config.ini
    config_file_path = os.path.join(script_directory, 'config.ini')

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read(config_file_path)

    return config


def kafka_producer(message, topic, bootstrap_servers):
    producer = Producer({'bootstrap.servers': bootstrap_servers})
    producer.produce(topic, key='my_key', value=message)
    producer.flush()


def kafka_consumer(topic, group_id, callback, bootstrap_servers, container_name):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })

    # Create an AdminClient for topic management
    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})

    # Check if the topic exists
    topic_metadata = admin_client.list_topics(timeout=5)
    if topic not in topic_metadata.topics:
        # Create the topic if it doesn't exist
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        admin_client.create_topics([new_topic])

        # Wait for topic creation to complete
        while topic not in admin_client.list_topics().topics:
            time.sleep(0.1)

    # Subscribe to the topic
    consumer.subscribe([topic])

    try:
        while True:
            msg = consumer.poll(1.0)

            if msg is None:
                continue
            if msg.error():
                if msg.error().code() == KafkaError._PARTITION_EOF:
                    continue
                else:
                    logger.error("Kafka error: %s", msg.error().str())
                    continue

            logger.info("Received message on topic '%s': %s",
                        topic, msg.value().decode())

            if callback.__name__ == 'create_docker_container':
                callback(msg.value().decode(), container_name)
            else:
                callback(container_name)

    finally:
        consumer.close()


def create_docker_container(file_path, container_name):
    try:
        # Create a Docker client
        client = docker.from_env()

        # Build the Docker image from the provided file
        image, _ = client.images.build(path=file_path, tag=container_name)

        # Start the Docker container with the desired command
        container = client.containers.run(
            image,
            detach=True,
            cap_add=["NET_ADMIN"],
            network=test_network_name,
            name=test_container_name
        )

        # Execute the file inside the container
        exec_command = f"docker exec -d {container.id} /bin/bash -c 'chmod +x {file_path} && {file_path}'"
        os.system(exec_command)

        logger.info("File executed inside the Docker container: %s", file_path)
    except docker.errors.APIError as e:
        logger.error("Failed to start Docker container: %s", e)


def list_containers_on_network(network_name):
    try:
        # Create a Docker client
        client = docker.from_env()

        # List the containers on the specified network
        containers = client.containers.list(filters={"network": network_name})

        # Containers data
        containers_data = []

        # Print the container information
        for container in containers:
            containers_data.append({
                "name": container.name,
                "status": container.status,
                "ip_address": container.attrs["NetworkSettings"]["Networks"][network_name]["IPAddress"]
            })

        return containers_data
    except docker.errors.APIError as e:
        logger.error("Failed to list containers on the network: %s", e)


def monitor_containers_on_network(kafka_url, network_name, monitoring_interval):
    while True:
        containers_data = list_containers_on_network(network_name)
        kafka_producer(json.dumps(containers_data),
                       'containers-data', kafka_url)

        time.sleep(monitoring_interval)


def main():
    # Load the configuration
    config = load_config()

    # Extract configuration values
    kafka_url = config.get('kafka', 'bootstrap_servers')
    container_name = 'my-container'
    network_name = 'my-network'
    monitoring_interval = 5

    # Start the Kafka consumer in a separate thread
    consumer_thread = threading.Thread(target=kafka_consumer, args=(
        'create-container', 'my-group-create-container', create_docker_container, kafka_url, container_name))
    consumer_thread.start()

    # List the containers on the network in a separate thread
    monitor_thread = threading.Thread(
        target=monitor_containers_on_network, args=(kafka_url, network_name, monitoring_interval))
    monitor_thread.start()

    # Check if the threads are alive
    while True:
        if not consumer_thread.is_alive():
            logger.error("The Kafka consumer thread is not alive")
            break
        if not monitor_thread.is_alive():
            logger.error("The monitor thread is not alive")
            break

        time.sleep(1)


if __name__ == '__main__':
    main()
