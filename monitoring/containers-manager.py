import json
import logging
import os
import signal
import sys
import time

from confluent_kafka import Producer, Consumer

from configuration import config_loader
from containers import docker_client
from kafka.kafka_client import consume_kafka_message, create_kafka_producer, create_kafka_consumer, FeedbackMessage, \
    Level
from threads.thread_pool import ThreadPool

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)


# Cleanup method before exiting the application
def cleanup_task(containers_data_producer: Producer, create_container_consumer: Consumer,
                 delete_container_consumer: Consumer):
    # Close Kafka producer and consumer
    containers_data_producer.flush()

    create_container_consumer.close()
    delete_container_consumer.close()
    logger.info("Kafka producer and consumer closed")


# Signal handler
def stop_threads_handler(thread_pool: ThreadPool,
                         containers_data_producer: Producer,
                         create_container_consumer: Consumer,
                         delete_container_consumer: Consumer):
    def signal_handler(sig, frame):
        logger.info("Interrupt signal received. Stopping application...")
        thread_pool.stop_threads()
        cleanup_task(containers_data_producer, create_container_consumer, delete_container_consumer)

    return signal_handler


def monitor_containers_task(producer: Producer, network_name: str, monitoring_interval: int = 5):
    logger.debug("Start 'monitor_containers_task' task...")

    try:
        containers_data = docker_client.list_containers_on_network(
            network_name)

        logger.info("Containers on network '%s': %d",
                    network_name, len(containers_data))

        containers_data = json.dumps([data.to_dict() for data in containers_data])

        producer.produce('containers-data', key='my_key',
                         value=containers_data)

        time.sleep(monitoring_interval)

    except Exception as e:
        logger.error("Error monitoring containers: %s", e)


def create_container_task(consumer: Consumer, containers_data_producer: Producer,
                          base_image_path: str, network_name: str):
    logger.debug("Start 'create_container_task' task...")

    try:
        message = consume_kafka_message(consumer)
        if message is None:
            return

        logger.info("Creating container with message: %s", message)
        docker_client.create_docker_container(base_image_path=base_image_path, network_name=network_name,
                                              create_request=message)

        logger.info("Container created successfully")
        feedback: FeedbackMessage = FeedbackMessage("Container created successfully", Level.SUCCESS)
        containers_data_producer.produce('containers-data-feedback', key='my_key', value=feedback.to_json())

    except Exception as e:
        logger.error("Error creating container: %s", e)
        feedback: FeedbackMessage = FeedbackMessage(str(e), Level.ERROR)
        containers_data_producer.produce('containers-data-feedback', key='my_key', value=feedback.to_json())


def delete_container_task(consumer: Consumer, containers_data_producer: Producer):
    logger.debug("Start 'delete_container_task' task...")

    try:
        message = consume_kafka_message(consumer)
        if message is None:
            return

        logger.info("Deleting container with id: %s", message)
        docker_client.delete_docker_container(container_id=message)

        logger.info("Container deleted successfully")
        feedback: FeedbackMessage = FeedbackMessage("Container deleted successfully", Level.SUCCESS)
        containers_data_producer.produce('containers-data-feedback', key='my_key', value=feedback.to_json())

    except Exception as e:
        logger.error("Error deleting container: %s", e)
        pass


def main():
    # Load the configuration
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')
    base_image_path = config.get('docker', 'base_image_path')

    monitoring_interval = 5

    # Init Kafka producer
    containers_data_producer = create_kafka_producer(kafka_url)

    # Init Kafka consumer
    create_container_consumer = create_kafka_consumer('create-container', 'my-group-create-container',
                                                      kafka_url)

    delete_container_consumer = create_kafka_consumer('delete-container', 'my-group-delete-container',
                                                      kafka_url)

    # Create thread pool
    thread_pool = ThreadPool(monitor_interval=monitoring_interval)

    # Add tasks to thread pool
    thread_pool.add_task(name='monitor_containers', target=monitor_containers_task,
                         args=(containers_data_producer, network_name, monitoring_interval))

    thread_pool.add_task(name='create_container', target=create_container_task,
                         args=(create_container_consumer, containers_data_producer, base_image_path, network_name))

    thread_pool.add_task(name='delete_container', target=delete_container_task,
                         args=(delete_container_consumer, containers_data_producer))

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, stop_threads_handler(
        thread_pool=thread_pool,
        containers_data_producer=containers_data_producer,
        create_container_consumer=create_container_consumer,
        delete_container_consumer=delete_container_consumer))

    # Start the threads
    thread_pool.start_threads()

    # Monitor threads
    thread_pool.monitor_threads()

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
