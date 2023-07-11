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
from kafka.kafka_client import consume_kafka_message, create_kafka_producer, create_kafka_consumer

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to stop threads
stop_threads = False


# Signal handler
def signal_handler(sig, frame):
    global stop_threads
    stop_threads = True
    logger.info("Interrupt signal received. Stopping threads...")


def monitor_containers_task(producer: Producer, network_name: str, monitoring_interval: int = 5):
    global stop_threads

    try:
        while not stop_threads:
            containers_data = docker_client.list_containers_on_network(
                network_name)

            logger.info("Containers on network '%s': %d",
                        network_name, len(containers_data))

            containers_data = json.dumps(
                [data.to_dict() for data in containers_data])

            producer.produce('containers-data', key='my_key',
                             value=containers_data)

            time.sleep(monitoring_interval)

    except KeyboardInterrupt:
        logger.info("Stopping thread 'monitor_containers_task'...")
        pass

    except Exception as e:
        logger.error("Error monitoring containers: %s", e)
        pass

    logger.info("Stopping thread 'monitor_containers_task'...")


def create_container_task(consumer: Consumer, base_image_path: str, network_name: str):
    global stop_threads

    try:
        while not stop_threads:
            message = consume_kafka_message(consumer)
            if message is None:
                continue

            logger.info("Creating container with message: %s", message)
            docker_client.create_docker_container(base_image_path=base_image_path, network_name=network_name,
                                                  create_request=message)

            logger.info("Container created successfully")

    except KeyboardInterrupt:
        logger.info("Stopping thread 'create_container_task'...")
        pass

    except Exception as e:
        logger.error("Error creating container: %s", e)
        pass

    logger.info("Stopping thread 'create_container_task'...")


def delete_container_task(consumer: Consumer):
    global stop_threads

    try:
        while not stop_threads:
            message = consume_kafka_message(consumer)
            if message is None:
                continue

            logger.info("Deleting container with id: %s", message)
            docker_client.delete_docker_container(container_id=message)
            logger.info("Container deleted successfully")

    except KeyboardInterrupt:
        logger.info("Stopping thread 'delete_container_task'...")
        pass

    logger.info("Stopping thread 'delete_container_task'...")


def build_delete_container_task(delete_container_consumer) -> threading.Thread:
    return threading.Thread(target=delete_container_task, args=(delete_container_consumer,))


def build_create_container_task(base_image_path, create_container_consumer, network_name) -> threading.Thread:
    return threading.Thread(target=create_container_task,
                            args=(create_container_consumer, base_image_path, network_name))


def build_monitor_containers_task(containers_data_producer, monitoring_interval, network_name) -> threading.Thread:
    return threading.Thread(target=monitor_containers_task,
                            args=(containers_data_producer, network_name, monitoring_interval))


def main():
    global stop_threads

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

    # Create threads
    threads = {
        'monitor_containers': build_monitor_containers_task(containers_data_producer, monitoring_interval,
                                                            network_name),
        'create_container': build_create_container_task(base_image_path, create_container_consumer,
                                                        network_name),
        'delete_container': build_delete_container_task(delete_container_consumer)
    }

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start the threads
    for thread_name, thread in threads.items():
        logger.info("Starting thread '%s'...", thread_name)
        thread.start()

    try:
        while not stop_threads:
            for thread_name, thread in threads.items():
                if not thread.is_alive():
                    logger.error("Thread '%s' is not alive. Restarting...", thread_name)

                    if thread_name == 'monitor_containers':
                        threads[thread_name] = build_monitor_containers_task(containers_data_producer,
                                                                             monitoring_interval,
                                                                             network_name)

                    elif thread_name == 'create_container':
                        threads[thread_name] = (base_image_path, create_container_consumer,
                                                network_name)

                    elif thread_name == 'delete_container':
                        threads[thread_name] = build_delete_container_task(
                            delete_container_consumer)

                    threads[thread_name].start()

            time.sleep(monitoring_interval)
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
    finally:
        for thread_name, thread in threads.items():
            logger.info("Stopping thread '%s'...", thread_name)
            thread.join()

        # Close Kafka producer and consumer
        containers_data_producer.flush()

        create_container_consumer.close()
        delete_container_consumer.close()

        logger.info("All threads stopped. Exiting...")

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
