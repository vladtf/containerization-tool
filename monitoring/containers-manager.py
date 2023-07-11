import signal
import sys
import time
import json
import logging

from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import threading
import os

from configuration import config_loader
from containers import docker_client

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger(__name__)

# Global variable to stop threads
stop_threads = False


def signal_handler(sig, frame):
    global stop_threads
    stop_threads = True
    logger.info("Interrupt signal received. Stopping threads...")


def create_kafka_producer(bootstrap_servers: str) -> Producer:
    producer = Producer({'bootstrap.servers': bootstrap_servers})
    return producer


def consume_kafka_message(consumer: Consumer):
    messages = consumer.consume(num_messages=1, timeout=1.0)
    if messages is None or len(messages) == 0:
        return

    if len(messages) > 1:
        logger.warning(
            "More than one message received. Consuming only the first one")

    message = messages[0]

    if message.error():
        logger.error("Consumer error: %s", message.error())
        return

    logger.debug("Consumed message: %s", message.value().decode('utf-8'))
    consumer.commit()

    return message.value().decode('utf-8')


def create_kafka_consumer(topic: str, group_id: str, bootstrap_servers: str):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    topic_metadata = admin_client.list_topics(timeout=5)

    if topic not in topic_metadata.topics:
        create_missing_topic(admin_client, topic)

    consumer.subscribe([topic])
    logger.info("Subscribed to topic '%s'", topic)

    return consumer


def create_missing_topic(admin_client, topic):
    new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
    admin_client.create_topics([new_topic])
    while topic not in admin_client.list_topics().topics:
        time.sleep(0.1)
    logger.info("Topic '%s' created", topic)


def monitor_containers_task(producer: Producer, network_name: str, monitoring_interval: int = 5):
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


def main():
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
        'monitor_containers': buildMonitorContainersTask(containers_data_producer, monitoring_interval, network_name),
        'create_container': buildCreateContainerTask(base_image_path, create_container_consumer, network_name),
        'delete_container': buildDeleteContainerTask(delete_container_consumer)
    }

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    for thread in threads.values():
        logger.info("Starting thread '%s'...", thread.name)
        thread.start()

    try:
        while not stop_threads:
            for thread_name, thread in threads.items():
                if not thread.is_alive():
                    logger.error(
                        "Thread '%s' is not alive. Restarting...", thread_name)

                    if thread_name == 'monitor_containers':
                        threads[thread_name] = buildMonitorContainersTask(containers_data_producer, monitoring_interval,
                                                                          network_name)

                    elif thread_name == 'create_container':
                        threads[thread_name] = buildCreateContainerTask(base_image_path, create_container_consumer,
                                                                        network_name)

                    elif thread_name == 'delete_container':
                        threads[thread_name] = buildDeleteContainerTask(
                            delete_container_consumer)

                    threads[thread_name].start()

            time.sleep(monitoring_interval)
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")
    finally:
        for thread in threads.values():
            thread.join()

        # Close Kafka producer and consumer
        containers_data_producer.flush()

        create_container_consumer.close()
        delete_container_consumer.close()

        logger.info("All threads stopped. Exiting...")

    logger.info("Exiting...")
    sys.exit(0)


def buildDeleteContainerTask(delete_container_consumer):
    return threading.Thread(target=delete_container_task, args=(delete_container_consumer,))


def buildCreateContainerTask(base_image_path, create_container_consumer, network_name):
    return threading.Thread(target=create_container_task,
                            args=(create_container_consumer, base_image_path, network_name))


def buildMonitorContainersTask(containers_data_producer, monitoring_interval, network_name):
    return threading.Thread(target=monitor_containers_task,
                            args=(containers_data_producer, network_name, monitoring_interval))


if __name__ == '__main__':
    main()
