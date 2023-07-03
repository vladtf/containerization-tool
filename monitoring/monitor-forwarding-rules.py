import time
import json
from confluent_kafka import Producer, Consumer, KafkaError
import docker
import threading


def kafka_producer(message, topic):
    bootstrap_servers = 'localhost:29092'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()


def kafka_consumer_add_rules():
    bootstrap_servers = 'localhost:29092'
    topic = 'add-forwarding-rules'
    group_id = 'my-group-add-rules'

    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })

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
                    print("Kafka error: {}".format(msg.error().str()))
                    continue

            print("Received message on 'add-forwarding-rules' topic: {}".format(msg.value().decode()))
            process_message_from_kafka(msg.value().decode())

    finally:
        consumer.close()


def kafka_consumer_clear_rules():
    bootstrap_servers = 'localhost:29092'
    topic = 'clear-forwarding-rules'
    group_id = 'my-group-clear-rules'

    consumer = Consumer({
        'bootstrap.servers': bootstrap_servers,
        'group.id': group_id,
        'auto.offset.reset': 'earliest'
    })

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
                    print("Kafka error: {}".format(msg.error().str()))
                    continue

            print("Received message on 'clear-forwarding-rules' topic: {}".format(msg.value().decode()))
            clear_nat_table()
            print("NAT table cleared.")

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


def clear_nat_table():
    # Logic to clear the NAT table
    # Replace 'my-ubuntu' with your actual container name
    container_name = 'my-ubuntu'
    client = docker.from_env()
    container = client.containers.get(container_name)

    exec_command = 'iptables -t nat -F OUTPUT'
    container.exec_run(exec_command, privileged=True)


def process_message_from_kafka(message):
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
        # Replace 'my-ubuntu' with your actual container name
        container_name = 'my-ubuntu'
        client = docker.from_env()
        container = client.containers.get(container_name)

        # iptables -t nat -A OUTPUT -d 8.8.8.8 -j DNAT --to-destination 9.9.9.9
        exec_command = f'iptables -t nat -A {chain_name} -d {source} -j {target} --to-destination {destination}'
        container.exec_run(exec_command, privileged=True)

        print(f"Iptables rule added: {exec_command}")
    except json.JSONDecodeError as e:
        print(f"Error parsing JSON: {e}")
    except KeyError as e:
        print(f"Key not found in JSON: {e}")
    except docker.errors.NotFound:
        print(f"Container '{container_name}' not found.")


# Replace 'my-ubuntu' with your actual container name
container_name = 'my-ubuntu'

# Set the monitoring interval (in seconds)
monitoring_interval = 5


def monitoring_thread():
    while True:
        nat_table = show_nat_table(container_name)
        # print(json.dumps(nat_table, indent=4))  # Display NAT table as JSON

        kafka_producer(json.dumps(nat_table, indent=4), 'monitor-forwarding-rules')

        time.sleep(monitoring_interval)


# Start the Kafka consumers in separate threads
consumer_thread_add_rules = threading.Thread(target=kafka_consumer_add_rules)
consumer_thread_clear_rules = threading.Thread(target=kafka_consumer_clear_rules)

consumer_thread_add_rules.start()
consumer_thread_clear_rules.start()

# Run the monitoring loop in the main thread
monitoring_thread()
