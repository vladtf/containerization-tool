import json
import logging
import os
import signal
import sys
import threading
import time

from confluent_kafka import Producer, Consumer

from configuration import config_loader
from containers import docker_client
from containers.docker_client import ContainerData
from kafka.kafka_client import consume_kafka_message, create_kafka_producer, create_kafka_consumer, Level, \
    send_feedback_message
from threads.thread_pool import ThreadPool

# Topics
CONTAINERS_DATA_TOPIC = "containers-data"
CREATE_CONTAINER_TOPIC = "create-container"
DELETE_CONTAINER_TOPIC = "delete-container"
CONTAINERS_DATA_FEEDBACK_TOPIC = "containers-data-feedback"
DEPLOY_CONTAINER_TOPIC = "deploy-container"

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


# Cleanup method before exiting the application
def cleanup_task(containers_data_producer: Producer, create_container_consumer: Consumer,
                 delete_container_consumer: Consumer, deploy_container_consumer: Consumer):
    # Close Kafka producer and consumer
    containers_data_producer.flush()

    create_container_consumer.close()
    delete_container_consumer.close()
    deploy_container_consumer.close()
    logger.info("Kafka producer and consumer closed")


# Signal handler
def stop_threads_handler(thread_pool: ThreadPool,
                         containers_data_producer: Producer,
                         create_container_consumer: Consumer,
                         delete_container_consumer: Consumer,
                         deploy_container_consumer: Consumer):
    def signal_handler(sig, frame):
        logger.info("Interrupt signal received. Stopping application...")
        thread_pool.stop_threads()
        cleanup_task(containers_data_producer,
                     create_container_consumer, delete_container_consumer, deploy_container_consumer)

    return signal_handler


def monitor_containers_task(containers_data_producer: Producer, network_name: str, monitoring_interval: int = 5):
    logger.debug("Start 'monitor_containers_task' task...")

    try:
        containers_data = docker_client.list_containers_on_network(
            network_name)

        logger.info("Containers on network '%s': %d",
                    network_name, len(containers_data))

        containers_data = json.dumps([data.to_dict()
                                      for data in containers_data])

        containers_data_producer.produce(CONTAINERS_DATA_TOPIC, key='my_key',
                                         value=containers_data)

        time.sleep(monitoring_interval)

    except Exception as e:
        logger.error("Error monitoring containers: %s", e)
        send_feedback_message(
            level=Level.ERROR,
            message=f"Error monitoring containers: {e}",
            producer=containers_data_producer,
            topic=CONTAINERS_DATA_FEEDBACK_TOPIC
        )


def create_container_task(consumer: Consumer, containers_data_producer: Producer,
                          base_image_path: str, network_name: str,
                          fluentd_address: str, fluentd_format: str, fluentd_driver: str):
    logger.debug("Start 'create_container_task' task...")

    try:
        message = consume_kafka_message(consumer)
        if message is None:
            return

        create_request = json.loads(message)
        create_request['containerName'] = create_request['containerName'].replace(
            " ", "_").lower()

        def create_container():
            try:
                logger.info("Creating container with message: %s",
                            create_request)
                docker_client.create_docker_container(
                    create_request=create_request,
                    base_image_path=base_image_path, network_name=network_name,
                    fluentd_address=fluentd_address, fluentd_format=fluentd_format, fluentd_driver=fluentd_driver
                )

                logger.info("Container created successfully")

                send_feedback_message(
                    level=Level.SUCCESS,
                    message=f"Container '{create_request['containerName']}' created successfully",
                    producer=containers_data_producer,
                    topic=CONTAINERS_DATA_FEEDBACK_TOPIC
                )

            except Exception as exc:
                logger.error("Error creating container: %s", exc)

                send_feedback_message(
                    level=Level.ERROR,
                    message=f"Error creating container: {exc}",
                    producer=containers_data_producer,
                    topic=CONTAINERS_DATA_FEEDBACK_TOPIC
                )

        # Create a new thread for creating the container
        create_thread = threading.Thread(target=create_container)
        create_thread.start()

    except Exception as e:
        logger.error("Error creating container: %s", e)

        send_feedback_message(
            level=Level.ERROR,
            message=f"Error creating container: {e}",
            producer=containers_data_producer,
            topic=CONTAINERS_DATA_FEEDBACK_TOPIC
        )


def delete_container_task(delete_container_consumer: Consumer, containers_data_producer: Producer):
    logger.debug("Start 'delete_container_task' task...")

    try:
        message = consume_kafka_message(delete_container_consumer)
        if message is None:
            return

        container_id = message

        def delete_container():
            try:
                logger.info("Deleting container with id: %s", message)
                deleted_container = docker_client.get_container_data(container_id=container_id)
                deleted_container.status = "deleted"

                docker_client.delete_docker_container(
                    container_id=container_id)
                logger.info("Container deleted successfully")

                send_feedback_message(
                    level=Level.SUCCESS,
                    message=f"Container '{container_id}' deleted successfully",
                    producer=containers_data_producer,
                    topic=CONTAINERS_DATA_FEEDBACK_TOPIC
                )

                containers_data_producer.produce(CONTAINERS_DATA_TOPIC, key='my_key',
                                                 value=json.dumps([deleted_container.to_dict()]))

            except Exception as exc:
                logger.error("Error deleting container: %s", exc)

                send_feedback_message(
                    level=Level.ERROR,
                    message=f"Error deleting container: {exc}",
                    producer=containers_data_producer,
                    topic=CONTAINERS_DATA_FEEDBACK_TOPIC
                )

        # Create a new thread for deleting the container
        delete_thread = threading.Thread(target=delete_container)
        delete_thread.start()

    except Exception as e:
        logger.error("Error deleting container: %s", e)

        send_feedback_message(
            level=Level.ERROR,
            message=f"Error deleting container: {e}",
            producer=containers_data_producer,
            topic=CONTAINERS_DATA_FEEDBACK_TOPIC)


from azure.identity import DefaultAzureCredential
from azure.mgmt.containerinstance import ContainerInstanceManagementClient
from azure.mgmt.containerinstance.models import (ContainerGroup, Container, ContainerPort, IpAddress, Port,
                                                 ResourceRequirements, ImageRegistryCredential)


def deploy_container_task(consumer: Consumer, containers_data_producer: Producer):
    logger.debug("Start 'deploy_container_task' task...")

    try:
        message = consume_kafka_message(consumer)

        if message is None:
            return

        containerData: ContainerData = ContainerData.from_dict(json.loads(message))

        logger.info("Deploying container: %s", containerData)
        credential = DefaultAzureCredential()
        subscription_id = "ae68c2fa-17e3-48cc-bf21-4e4511e416ac"
        resource_group = "containerization-tool"
        location = "UK South"

        # Create a container instance
        container_group_name = "container-test-ping-sh"
        container_image = "containerizationtool.azurecr.io/container-test-ping.sh_image:latest"

        # Configure the container properties
        container = Container(
            name="container-test-ping-sh",
            image=container_image,
            resources=ResourceRequirements(requests={"cpu": "1.0", "memoryInGB": "1.5"}),
            ports=[ContainerPort(port=80)],
        )

        # Image registry credentials configuration
        acr_server = "containerizationtool.azurecr.io"
        acr_username = "placeholder"
        acr_password = "placeholder"

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


    except Exception as exc:
        logger.error("Error deploying container: %s", exc)

        send_feedback_message(
            level=Level.ERROR,
            message=f"Error deploying container: {exc}",
            producer=containers_data_producer,
            topic=CONTAINERS_DATA_FEEDBACK_TOPIC
        )


def main():
    # Load the configuration
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')
    base_image_path = config.get('docker', 'base_image_path')
    fluentd_address = config.get('fluentd', 'address')
    fluentd_format = config.get('fluentd', 'format')
    fluentd_driver = config.get('fluentd', 'driver')

    monitoring_interval = 5

    # Init Kafka producer
    containers_data_producer = create_kafka_producer(kafka_url)

    # Init Kafka consumer
    create_container_consumer = create_kafka_consumer(CREATE_CONTAINER_TOPIC, 'my-group-create-container',
                                                      kafka_url)

    delete_container_consumer = create_kafka_consumer(DELETE_CONTAINER_TOPIC, 'my-group-delete-container',
                                                      kafka_url)

    deploy_container_consumer = create_kafka_consumer(DEPLOY_CONTAINER_TOPIC, 'my-group-deploy-container',
                                                        kafka_url)

    # Create thread pool
    thread_pool = ThreadPool(monitor_interval=monitoring_interval)

    # Add tasks to thread pool
    thread_pool.add_task(name='monitor_containers', target=monitor_containers_task,
                         args=(containers_data_producer, network_name, monitoring_interval))

    thread_pool.add_task(name='create_container', target=create_container_task,
                         args=(create_container_consumer, containers_data_producer, base_image_path, network_name,
                               fluentd_address, fluentd_format, fluentd_driver))

    thread_pool.add_task(name='delete_container', target=delete_container_task,
                         args=(delete_container_consumer, containers_data_producer))

    thread_pool.add_task(name='deploy_container', target=deploy_container_task,
                         args=(deploy_container_consumer, containers_data_producer))

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, stop_threads_handler(
        thread_pool=thread_pool,
        containers_data_producer=containers_data_producer,
        create_container_consumer=create_container_consumer,
        delete_container_consumer=delete_container_consumer,
        deploy_container_consumer=deploy_container_consumer))

    # Start the threads
    thread_pool.start_threads()

    # Monitor threads
    thread_pool.monitor_threads()

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
