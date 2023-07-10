import subprocess
import re
import json
import logging
from confluent_kafka import Producer
import pyshark
import configparser
import os
import time
import threading

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("monitor-docker-traffic")

# Counter variable to keep track of the message count
message_count = 0


def load_config():
    # Get the directory path of the script
    script_directory = os.path.dirname(os.path.abspath(__file__))

    # Construct the absolute path to config.ini
    config_file_path = os.path.join(script_directory, 'config.ini')

    # Read the configuration file
    config = configparser.ConfigParser()
    config.read(config_file_path)

    return config


def get_docker_interface(docker_network_name):
    command = ['docker', 'network', 'ls',
               '--filter', f"name={docker_network_name}"]
    result = subprocess.run(command, capture_output=True, text=True)

    match = re.search(r"(\w{12})", result.stdout)
    if match:
        interface_id = match.group(1)
        return "br-" + interface_id

    return None


def kafka_producer(message, bootstrap_servers):
    global message_count
    topic = 'monitor-docker-traffic'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()

    # Increment the message count
    message_count += 1


def packet_callback(pkt, config):
    packet_data = {}

    if 'ip' in pkt:
        packet_data['protocol'] = 'ip'
        packet_data['src_ip'] = pkt.ip.src
        packet_data['dst_ip'] = pkt.ip.dst

        if 'tcp' in pkt:
            packet_data['protocol'] = 'tcp'
            packet_data['src_port'] = pkt.tcp.srcport
            packet_data['dst_port'] = pkt.tcp.dstport

        elif 'udp' in pkt:
            packet_data['protocol'] = 'udp'
            packet_data['src_port'] = pkt.udp.srcport
            packet_data['dst_port'] = pkt.udp.dstport

    elif 'ipv6' in pkt:
        packet_data['protocol'] = 'ipv6'
        packet_data['src_ip'] = pkt.ipv6.src
        packet_data['dst_ip'] = pkt.ipv6.dst

        if 'tcp' in pkt:
            packet_data['protocol'] = 'tcp'
            packet_data['src_port'] = pkt.tcp.srcport
            packet_data['dst_port'] = pkt.tcp.dstport

        elif 'udp' in pkt:
            packet_data['protocol'] = 'udp'
            packet_data['src_port'] = pkt.udp.srcport
            packet_data['dst_port'] = pkt.udp.dstport

    elif 'arp' in pkt:
        packet_data['protocol'] = 'arp'
        packet_data['src_mac'] = pkt.arp.src_hw_mac
        packet_data['dst_mac'] = pkt.arp.dst_hw_mac

    elif 'icmp' in pkt:
        packet_data['protocol'] = 'icmp'
        packet_data['src_ip'] = pkt.icmp.src
        packet_data['dst_ip'] = pkt.icmp.dst

    else:
        packet_data['protocol'] = 'unknown'

    json_message = json.dumps(packet_data)
    kafka_url = config.get('kafka', 'bootstrap_servers')
    kafka_producer(json_message, kafka_url)

# Periodically log the message count


def log_message_count():
    global message_count
    while True:
        logger.info("Total Messages Sent: %d", message_count)
        message_count = 0
        time.sleep(1)


def main():
    # Load the configuration
    config = load_config()

    # Get Kafka URL from the configuration
    kafka_url = config.get('kafka', 'bootstrap_servers')

    # Docker network name
    docker_network_name = 'mynetwork'

    # Get the Docker network interface name
    interface = get_docker_interface(docker_network_name)

    # Log the interface name
    if interface:
        logger.info("Docker network interface name: %s", interface)
    else:
        logger.error("Failed to retrieve Docker network interface name.")

    if interface:
        # Start the message count logging thread
        thread = threading.Thread(target=log_message_count)
        thread.start()

        # Set up the packet capture
        capture = pyshark.LiveCapture(interface=interface)

        # Start capturing packets and invoke the packet_callback function for each packet
        capture.apply_on_packets(lambda pkt: packet_callback(pkt, config))


if __name__ == '__main__':
    main()
