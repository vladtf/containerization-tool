import signal
import sys
import time
import json
import logging
from confluent_kafka import Producer, Consumer, KafkaError
import docker
import threading
from confluent_kafka.admin import AdminClient, NewTopic
import os

from configuration import config_loader
from containers.docker_client import list_containers_on_network
from kafka.kafka_client import create_kafka_producer, create_kafka_consumer, consume_kafka_message

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("monitor-forwarding-rules")

# Global variable to stop threads
stop_threads = False


# Signal handler
def signal_handler(sig, frame):
    global stop_threads
    stop_threads = True
    logger.info("Interrupt signal received. Stopping threads...")


def show_nat_table(container_id):
    client = docker.from_env()
    container = client.containers.get(container_id)

    exec_command = 'iptables-save -t nat'
    response = container.exec_run(exec_command, privileged=True)

    output = response.output.decode()

    nat_table = parse_iptables_rules(output)

    return nat_table


def parse_iptables_rules(iptables_output):
    rules = iptables_output.strip().split('\n')
    nat_table = []
    chain = None

    for rule in rules:
        rule = rule.strip()
        if rule.startswith(':'):
            # Skip the counters line
            continue

        if rule.startswith('-A'):
            parts = rule.split(' ')
            chain = parts[1]
            rule_spec = parts[2:]

            # TODO: handle other chains
            if chain != 'OUTPUT':
                continue

            rule_entry = {
                'command': rule,
                'chain': chain,
                'target': None,
                'protocol': None,
                'options': None,
                'source': None,
                'destination': None
            }

            # Extracting the target, protocol, options, source, and destination from the rule_spec
            for i, part in enumerate(rule_spec):
                if part == '-j':
                    rule_entry['target'] = rule_spec[i + 1]
                elif part == '-p':
                    rule_entry['protocol'] = rule_spec[i + 1]
                elif part == '-s':
                    rule_entry['source'] = rule_spec[i + 1]
                elif part == '-d':
                    rule_entry['source'] = rule_spec[i + 1]
                elif part == '--to-destination':
                    rule_entry['destination'] = rule_spec[i + 1]

            # Add the rule to the nat table
            nat_table.append(rule_entry)

    return nat_table


def clear_nat_table_task(clear_forwarding_rules_consumer: Consumer):
    global stop_threads

    try:
        while not stop_threads:
            message = consume_kafka_message(clear_forwarding_rules_consumer)
            if message is None:
                continue

            parsed_message = json.loads(message)
            container_id = parsed_message['containerId']

            client = docker.from_env()
            container = client.containers.get(container_id)

            exec_command = 'iptables -t nat -F OUTPUT'
            container.exec_run(exec_command, privileged=True)

            logger.info("NAT table cleared: %s", exec_command)
    except KeyboardInterrupt:
        logger.info("Stopping thread 'clear_nat_table'...")
        pass

    except Exception as e:
        logger.error("Error clearing NAT table", e)
        pass

    logger.info("Thread 'clear_nat_table' stopped.")


def add_forwarding_rule_task(add_forwarding_rules_consumer):
    global stop_threads
    try:
        while not stop_threads:
            message = consume_kafka_message(add_forwarding_rules_consumer)
            if message is None:
                continue

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

    except KeyboardInterrupt:
        logger.info("Stopping thread 'process_message_from_kafka'...")
        pass

    except Exception as e:
        logger.error("Error processing message from Kafka: %s", e)
        pass

    logger.info("Thread 'process_message_from_kafka' stopped.")


def monitor_forwarding_rules_task(forwarding_rules_producer: Producer, network_name: str, monitoring_interval: int):
    global stop_threads

    try:
        while not stop_threads:

            containers = list_containers_on_network(network_name)

            nat_tables = []

            for container in containers:
                nat_table = show_nat_table(container.id)

                nat_tables.append({
                    'containerId': container.id,
                    'containerName': container.name,
                    'rules': nat_table
                })

                logger.info("NAT table for container '%s': %d rules",
                            container.name, len(nat_table))

            forwarding_rules_producer.produce(
                'forwarding-rules', key='my_key', value=json.dumps(nat_tables))

            logger.info("Sent %d nat tables to Kafka", len(nat_tables))
            time.sleep(monitoring_interval)
    except KeyboardInterrupt:
        logger.info("Stopping thread 'monitor_forwarding_rules'...")
        pass

    except Exception as e:
        logger.error("Error in thread 'monitor_forwarding_rules': %s", e)
        pass

    logger.info("Thread 'monitor_forwarding_rules' stopped.")


def build_monitor_forwarding_rules_task(monitoring_interval, network_name,
                                        forwarding_rules_producer) -> threading.Thread:
    return threading.Thread(target=monitor_forwarding_rules_task, args=(
        forwarding_rules_producer, network_name, monitoring_interval))


def build_clear_forwarding_rules_task(clear_forwarding_rules_consumer) -> threading.Thread:
    return threading.Thread(target=clear_nat_table_task, args=(clear_forwarding_rules_consumer,))


def build_add_forwarding_rules_task(add_forwarding_rules_consumer) -> threading.Thread:
    return threading.Thread(target=add_forwarding_rule_task, args=(add_forwarding_rules_consumer,))


def main():
    global stop_threads

    # Load the configuration
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    network_name = config.get('docker', 'network_name')

    monitoring_interval = 5

    # Init Kafka producer
    forwarding_rules_producer = create_kafka_producer(kafka_url)

    # Init Kafka consumer
    add_forwarding_rules_consumer = create_kafka_consumer(
        'add-forwarding-rules', 'my-group-add-rules', kafka_url)

    clear_forwarding_rules_consumer = create_kafka_consumer(
        'clear-forwarding-rules', 'my-group-clear-rules', kafka_url)

    # Create threads
    threads = {
        'add-forwarding-rules': build_add_forwarding_rules_task(add_forwarding_rules_consumer),
        'clear-forwarding-rules': build_clear_forwarding_rules_task(clear_forwarding_rules_consumer),
        'monitor-forwarding-rules': build_monitor_forwarding_rules_task(monitoring_interval, network_name,
                                                                        forwarding_rules_producer)
    }

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start the threads
    for thread_name, thread in threads.items():
        logger.info("Starting thread '%s'", thread_name)
        thread.start()

    try:
        while not stop_threads:
            for thread_name, thread in threads.items():
                if not thread.is_alive():
                    logger.error("Thread '%s' is not alive. Restarting...", thread_name)

                    if thread_name == 'monitor-forwarding-rules':
                        threads[thread_name] = build_monitor_forwarding_rules_task(monitoring_interval, network_name,
                                                                                   forwarding_rules_producer)
                    elif thread_name == 'add-forwarding-rules':
                        threads[thread_name] = build_add_forwarding_rules_task(add_forwarding_rules_consumer)
                    elif thread_name == 'clear-forwarding-rules':
                        threads[thread_name] = build_clear_forwarding_rules_task(clear_forwarding_rules_consumer)

                    threads[thread_name].start()

            time.sleep(monitoring_interval)
    except KeyboardInterrupt:
        logger.info("Stopping threads...")
    finally:
        for thread in threads.values():
            logger.info("Stopping thread '%s'...", thread.name)
            thread.join()

        # Close Kafka producer and consumer
        forwarding_rules_producer.flush()

        add_forwarding_rules_consumer.close()
        clear_forwarding_rules_consumer.close()

        logger.info("All threads stopped. Exiting...")

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
