import signal
import time
import json
import logging
from typing import Callable
from functools import partial
from confluent_kafka import Producer, Consumer, KafkaError
from confluent_kafka.admin import AdminClient, NewTopic
import threading
import os

from configuration import config_loader
from containers import docker_client

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("containers-manager")

# Flag to signal threads to stop
stop_threads = False


def signal_handler(sig, frame):
    global stop_threads
    stop_threads = True
    logger.info("Interrupt signal received. Stopping threads...")


def kafka_producer(message: str, topic: str, bootstrap_servers: str):
    producer = Producer({'bootstrap.servers': bootstrap_servers})
    producer.produce(topic, key='my_key', value=message)
    producer.flush()


def kafka_consumer(topic: str, group_id: str, callback: Callable[[str], None], bootstrap_servers: str):
    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest',
        'enable.auto.commit': False
    })

    admin_client = AdminClient({'bootstrap.servers': bootstrap_servers})
    topic_metadata = admin_client.list_topics(timeout=5)

    if topic not in topic_metadata.topics:
        new_topic = NewTopic(topic, num_partitions=1, replication_factor=1)
        admin_client.create_topics([new_topic])
        while topic not in admin_client.list_topics().topics:
            time.sleep(0.1)
        logger.info("Topic '%s' created", topic)
    consumer.subscribe([topic])

    try:
        while not stop_threads:
            messages = consumer.consume(10, timeout=1.0)
            for message in messages:
                if message is None:
                    continue
                if message.error():
                    if message.error().code() == KafkaError.PARTITION_EOF:
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


def monitor_containers_on_network(kafka_url: str, network_name: str, monitoring_interval: int):
    while not stop_threads:
        containers_data = docker_client.list_containers_on_network(
            network_name)

        containers_data = json.dumps([data.to_dict() for data in containers_data])

        kafka_producer(json.dumps(containers_data),
                       'containers-data', kafka_url)

        time.sleep(monitoring_interval)


def main():
    global stop_threads

    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')
    base_image_path = config.get('docker', 'base_image_path')

    monitoring_interval = 5

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    create_callback = prepare_docker_callback(
        docker_client.create_docker_container, base_image_path=base_image_path, network_name=network_name)
    delete_callback = prepare_docker_callback(
        docker_client.delete_docker_container)

    threads = {
        "consumer_thread": threading.Thread(target=kafka_consumer, args=(
            'create-container', 'my-group-create-container', create_callback, kafka_url)),
        "monitor_thread": threading.Thread(target=monitor_containers_on_network, args=(
            kafka_url, network_name, monitoring_interval)),
        "delete_consumer_thread": threading.Thread(target=kafka_consumer, args=(
            'delete-container', 'my-group-delete-container', delete_callback, kafka_url))
    }

    for thread in threads.values():
        thread.start()

    try:
        while not stop_threads:
            for thread_name, thread in threads.items():
                if not thread.is_alive():
                    logger.error(
                        "Thread '%s' is not alive. Restarting...", thread_name)
                    if thread_name == "consumer_thread":
                        threads[thread_name] = threading.Thread(target=kafka_consumer, args=(
                            'create-container', 'my-group-create-container', create_callback, kafka_url))
                    elif thread_name == "monitor_thread":
                        threads[thread_name] = threading.Thread(target=monitor_containers_on_network, args=(
                            kafka_url, network_name, monitoring_interval))
                    elif thread_name == "delete_consumer_thread":
                        threads[thread_name] = threading.Thread(target=kafka_consumer, args=(
                            'delete-container', 'my-group-delete-container', delete_callback, kafka_url))
                    threads[thread_name].start()
            time.sleep(1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")

    finally:
        stop_threads = True
        for thread_name, thread in threads.items():
            thread.join()
            logger.info("Thread '%s' has stopped.", thread_name)


if __name__ == '__main__':
    main()
