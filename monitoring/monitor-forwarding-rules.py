import json
import logging
import os
import signal
import sys
import time

import docker
from confluent_kafka import Producer, Consumer

from configuration import config_loader
from containers.docker_client import list_containers_on_network
from iptables.iptables_client import show_nat_table
from kafka.kafka_client import create_kafka_producer, create_kafka_consumer, consume_kafka_message, Level, \
    send_feedback_message
from threads.thread_pool import ThreadPool

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("monitor-forwarding-rules")

# Topics
ADD_FORWARDING_RULE_TOPIC = "add-forwarding-rules"
CLEAR_FORWARDING_RULES_TOPIC = "clear-forwarding-rules"
FORWARDING_RULES_FEEDBACK_TOPIC = "forwarding-rules-feedback"


# Cleanup method before exiting the application
def cleanup_task(forwarding_rules_producer: Producer,
                 add_forwarding_rules_consumer: Consumer,
                 clear_forwarding_rules_consumer: Consumer):
    # Close Kafka producer and consumer
    forwarding_rules_producer.flush()

    add_forwarding_rules_consumer.close()
    clear_forwarding_rules_consumer.close()

    logger.info("Kafka producer and consumer closed")


# Signal handler
def stop_threads_handler(thread_pool: ThreadPool,
                         forwarding_rules_producer: Producer,
                         add_forwarding_rules_consumer: Consumer,
                         clear_forwarding_rules_consumer: Consumer):
    def signal_handler(sig, frame):
        logger.info("Interrupt signal received. Stopping application...")
        thread_pool.stop_threads()
        cleanup_task(forwarding_rules_producer, add_forwarding_rules_consumer, clear_forwarding_rules_consumer)

    return signal_handler


def clear_nat_table_task(clear_forwarding_rules_consumer: Consumer, forwarding_rules_producer: Producer):
    try:
        message = consume_kafka_message(clear_forwarding_rules_consumer)
        if message is None:
            return

        parsed_message = json.loads(message)
        container_id = parsed_message['containerId']

        client = docker.from_env()
        container = client.containers.get(container_id)

        exec_command = 'iptables -t nat -F OUTPUT'
        container.exec_run(exec_command, privileged=True)

        logger.info("NAT table cleared: %s", exec_command)
        send_feedback_message(
            level=Level.SUCCESS,
            message="NAT table cleared",
            producer=forwarding_rules_producer,
            topic=FORWARDING_RULES_FEEDBACK_TOPIC
        )

    except Exception as e:
        logger.error("Error clearing NAT table", e)
        send_feedback_message(
            level=Level.ERROR,
            message=f"Error clearing NAT table: {e}",
            producer=forwarding_rules_producer,
            topic=FORWARDING_RULES_FEEDBACK_TOPIC
        )


def add_forwarding_rule_task(add_forwarding_rules_consumer: Consumer, forwarding_rules_producer: Producer):
    try:
        message = consume_kafka_message(add_forwarding_rules_consumer)
        if message is None:
            return

        parsed_message = json.loads(message)
        chain_name = parsed_message['chainName']
        container_id = parsed_message['containerId']
        rule = parsed_message['rule']

        # Extract the rule details
        target = rule['target']
        protocol = rule['protocol']
        source = rule['source']
        destination = rule['destination']

        # Update iptables with the rule
        client = docker.from_env()
        container = client.containers.get(container_id)

        exec_command = f'iptables -t nat -A {chain_name} -d {source} -j {target} --to-destination {destination}'
        container.exec_run(exec_command, privileged=True)

        logger.info("Iptables rule added: %s", exec_command)
        send_feedback_message(
            level=Level.SUCCESS,
            message="Iptables rule added",
            producer=forwarding_rules_producer,
            topic=FORWARDING_RULES_FEEDBACK_TOPIC
        )

    except Exception as e:
        logger.error("Error processing message from Kafka: %s", e)
        send_feedback_message(
            level=Level.ERROR,
            message=f"Error processing message from Kafka: {e}",
            producer=forwarding_rules_producer,
            topic=FORWARDING_RULES_FEEDBACK_TOPIC
        )


def monitor_forwarding_rules_task(forwarding_rules_producer: Producer, network_name: str, monitoring_interval: int):
    try:
        containers = list_containers_on_network(network_name)

        nat_tables = []

        for container in containers:
            if container.status != 'running':
                logger.warning("Container '%s' is not running. Skipping...", container.name)
                continue

            nat_table = show_nat_table(container.id)

            nat_tables.append({
                'containerId': container.id,
                'containerName': container.name,
                'rules': [rule.to_dict() for rule in nat_table]
            })

            logger.info("NAT table for container '%s': %d rules",
                        container.name, len(nat_table))

        forwarding_rules_producer.produce(
            'forwarding-rules', key='my_key', value=json.dumps(nat_tables))

        logger.info("Sent %d nat tables to Kafka", len(nat_tables))
        time.sleep(monitoring_interval)

    except Exception as e:
        logger.error("Error in thread 'monitor_forwarding_rules': %s", e)
        send_feedback_message(
            level=Level.ERROR,
            message=f"Error in thread 'monitor_forwarding_rules': {e}",
            producer=forwarding_rules_producer,
            topic=FORWARDING_RULES_FEEDBACK_TOPIC
        )


def main():
    # Load the configuration
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')

    monitoring_interval = 5

    # Init Kafka producer
    forwarding_rules_producer = create_kafka_producer(kafka_url)

    # Init Kafka consumer
    add_forwarding_rules_consumer = create_kafka_consumer(
        ADD_FORWARDING_RULE_TOPIC, 'my-group-add-rules', kafka_url)

    clear_forwarding_rules_consumer = create_kafka_consumer(
        CLEAR_FORWARDING_RULES_TOPIC, 'my-group-clear-rules', kafka_url)

    # Create threads
    thread_pool = ThreadPool(monitor_interval=monitoring_interval)

    # Add tasks to thread pool
    thread_pool.add_task(name='monitor_forwarding_rules', target=monitor_forwarding_rules_task,
                         args=(forwarding_rules_producer, network_name, monitoring_interval))

    thread_pool.add_task(name='add_forwarding_rules', target=add_forwarding_rule_task,
                         args=(add_forwarding_rules_consumer, forwarding_rules_producer))

    thread_pool.add_task(name='clear_forwarding_rules', target=clear_nat_table_task,
                         args=(clear_forwarding_rules_consumer, forwarding_rules_producer))

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, stop_threads_handler(
        thread_pool=thread_pool,
        forwarding_rules_producer=forwarding_rules_producer,
        add_forwarding_rules_consumer=add_forwarding_rules_consumer,
        clear_forwarding_rules_consumer=clear_forwarding_rules_consumer))

    # Start the threads
    thread_pool.start_threads()

    # Monitor threads
    thread_pool.monitor_threads()

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
