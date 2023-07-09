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

            if callback.__name__ == 'clear_nat_table':
                callback(container_name)
            else:
                callback(msg.value().decode(), container_name)

    finally:
        consumer.close()


def show_nat_table(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)

    exec_command = 'iptables-save -t nat'
    response = container.exec_run(exec_command, privileged=True)

    output = response.output.decode()

    nat_table = parse_iptables_rules(output)

    return nat_table


def parse_iptables_rules(iptables_output):
    rules = iptables_output.strip().split('\n')
    nat_table = {}
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

            nat_table.setdefault(chain, []).append(rule_entry)

    return nat_table


def clear_nat_table(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)

    exec_command = 'iptables -t nat -F OUTPUT'
    container.exec_run(exec_command, privileged=True)


def process_message_from_kafka(message, container_name):
    try:
        parsed_message = json.loads(message)
        chain_name = parsed_message['chainName']
        rule = parsed_message['rule']

        # Extract the rule details
        target = rule['target']
        protocol = rule['protocol']
        source = rule['source']
        destination = rule['destination']

        # Update iptables with the rule
        client = docker.from_env()
        container = client.containers.get(container_name)

        exec_command = f'iptables -t nat -A {chain_name} -d {source} -j {target} --to-destination {destination}'
        container.exec_run(exec_command, privileged=True)

        logger.info("Iptables rule added: %s", exec_command)
    except json.JSONDecodeError as e:
        logger.error("Error parsing JSON: %s", e)
    except KeyError as e:
        logger.error("Key not found in JSON: %s", e)
    except docker.errors.NotFound:
        logger.error("Container '%s' not found.", container_name)


def monitor_forwarding_rules(bootstrap_servers, container_name, monitoring_interval):
    while True:
        nat_table = show_nat_table(container_name)
        kafka_producer(json.dumps(nat_table, indent=4),
                       'monitor-forwarding-rules', bootstrap_servers)
        time.sleep(monitoring_interval)


def main():
    # Load the configuration
    config = load_config()

    # Extract configuration values
    kafka_url = config.get('kafka', 'bootstrap_servers')
    container_name = 'my-ubuntu'
    monitoring_interval = 5

    # Start the Kafka consumers in separate threads
    consumer_thread_add_rules = threading.Thread(target=kafka_consumer, args=(
        'add-forwarding-rules', 'my-group-add-rules', process_message_from_kafka, kafka_url, container_name))
    consumer_thread_clear_rules = threading.Thread(target=kafka_consumer, args=(
        'clear-forwarding-rules', 'my-group-clear-rules', clear_nat_table, kafka_url, container_name))

    consumer_thread_add_rules.start()
    consumer_thread_clear_rules.start()

    # Run the monitoring loop in separate thread
    # monitoring_thread(kafka_url, container_name, monitoring_interval)
    monitoring_thread = threading.Thread(target=monitor_forwarding_rules, args=(
        kafka_url, container_name, monitoring_interval))
    monitoring_thread.start()

    # Check if the threads are alive
    while True:
        if not consumer_thread_add_rules.is_alive():
            logger.error(
                "Consumer thread for 'add-forwarding-rules' topic is dead.")
            break
        if not consumer_thread_clear_rules.is_alive():
            logger.error(
                "Consumer thread for 'clear-forwarding-rules' topic is dead.")
            break
        if not monitoring_thread.is_alive():
            logger.error("Monitoring thread is dead.")
            break

        time.sleep(1)


if __name__ == '__main__':
    main()
