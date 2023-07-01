import time
import json
from confluent_kafka import Producer
import docker


def kakfa_producer(message):
    bootstrap_servers = 'localhost:29092'
    topic = 'monitor-forwarding-rules'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()

    print("Message sent to Kafka!")


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
            if len(parts) >= 9:
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


# Replace 'my-ubuntu' with your actual container name
container_name = 'my-ubuntu'

# Set the monitoring interval (in seconds)
monitoring_interval = 3

while True:
    nat_table = show_nat_table(container_name)
    # print(json.dumps(nat_table, indent=4))  # Display NAT table as JSON
    kakfa_producer(json.dumps(nat_table, indent=4))

    time.sleep(monitoring_interval)
