import time
import json
from confluent_kafka import Producer, Consumer, KafkaError
import docker
import threading


def kafka_producer(message):
    bootstrap_servers = 'localhost:29092'
    topic = 'monitor-forwarding-rules'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()

    # print("Message sent to Kafka: {}".format(message))
    # print("Message sent to Kafka")


def kafka_consumer():
    bootstrap_servers = 'localhost:29092'
    topic = 'add-forwarding-rules'
    group_id = 'my-group'

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

            print("Received message: {}".format(msg.value().decode()))
            process_message_from_kafka(msg.value().decode())
            

    finally:
        consumer.close()


def show_nat_table(container_name):
    client = docker.from_env()
    container = client.containers.get(container_name)

    exec_command = 'iptables -t nat -L -n --line-numbers'
    response = container.exec_run(exec_command, privileged=True)

    output = response.output.decode()

    nat_table = {}
    chain = None
    lines = output.strip().split('\n')
    for line in lines:
        if line.startswith('Chain'):
            chain = line.split()[1]
            nat_table[chain] = {}
        elif chain and not line.startswith('target'):
            parts = line.split()
            if len(parts) >= 8:
                rule_number = int(parts[0])
                target = parts[1]
                prot = parts[2]
                opt = parts[3]
                source = parts[4]
                destination = parts[5]
                extra = parts[6:]
                nat_table[chain][rule_number] = {
                    'target': target,
                    'protocol': prot,
                    'options': opt,
                    'source': source,
                    'destination': destination,
                    'extra': extra
                }

    return nat_table


def process_message_from_kafka(message):
    try:
        parsed_message = json.loads(message)
        chain_name = parsed_message['chainName']
        rule = parsed_message['rule']

        # Extract the rule details
        rule_name = rule['name']
        target = rule['target']
        protocol = rule['protocol']
        options = rule['options']
        source = rule['source']
        destination = rule['destination']
        extra = rule['extra']

        # Update iptables with the rule
        # Replace 'my-ubuntu' with your actual container name
        container_name = 'my-ubuntu'
        client = docker.from_env()
        container = client.containers.get(container_name)

        exec_command = f'iptables -t nat -A {chain_name} -p {protocol} -s {source} -d {destination} -j {target}'
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
monitoring_interval = 3


def monitoring_thread():
    while True:
        nat_table = show_nat_table(container_name)
        # print(json.dumps(nat_table, indent=4))  # Display NAT table as JSON

        kafka_producer(json.dumps(nat_table, indent=4))

        time.sleep(monitoring_interval)


# Start the Kafka consumer in a separate thread
consumer_thread = threading.Thread(target=kafka_consumer)
consumer_thread.start()

# Run the monitoring loop in the main thread
monitoring_thread()
