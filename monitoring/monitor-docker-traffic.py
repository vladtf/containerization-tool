import json
import logging
import os
import signal
import sys
import threading
import time

import docker
import pyshark
from confluent_kafka import Producer

from configuration import config_loader
from kafka.kafka_client import create_kafka_producer
from threads.thread_pool import ThreadPool

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("monitor-docker-traffic")

# Counter variable to keep track of the message count
message_count = 0


# Cleanup method before exiting the application
def cleanup_task(traffic_producer: Producer):
    # Close Kafka producer and consumer
    traffic_producer.flush()

    logger.info("Kafka producer and consumer closed")


# Signal handler
def stop_threads_handler(thread_pool: ThreadPool,
                         traffic_producer: Producer):
    def signal_handler(sig, frame):
        logger.info("Interrupt signal received. Stopping application...")
        thread_pool.stop_threads()
        cleanup_task(traffic_producer)

    return signal_handler


def get_docker_interface(docker_network_name):
    client = docker.from_env()

    network = client.networks.get(docker_network_name)

    if network is None:
        logger.error("Error getting docker interface")
        exit(1)

    bridge_interface = network.attrs['Options']['com.docker.network.bridge.name']

    return bridge_interface


def packet_callback(pkt, traffic_producer: Producer):
    global message_count

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

    traffic_producer.produce('monitor-docker-traffic', key='my_key', value=json_message)
    message_count += 1


# Periodically log the message count
def log_message_count_task(monitoring_interval: int = 5):
    global message_count

    logger.info("Total Messages Sent: %d", message_count)
    message_count = 0
    time.sleep(monitoring_interval)


def monitor_traffic_task(docker_network_name: str, traffic_producer: Producer):
    # Get the Docker network interface name
    interface = get_docker_interface(docker_network_name)

    # Log the interface name
    logger.info("Docker network interface name: %s", interface)

    # Set up the packet capture
    capture = pyshark.LiveCapture(interface=interface)

    # Start capturing packets and invoke the packet_callback function for each packet
    capture.apply_on_packets(lambda pkt: packet_callback(pkt, traffic_producer))


def main():
    # Load the configuration
    config = config_loader.load_config(os.path.abspath(__file__))
    kafka_url = config.get('kafka', 'bootstrap_servers')
    docker_network_name = config.get('docker', 'network_name')

    monitoring_interval = 5

    # Init Kafka producer
    traffic_producer = create_kafka_producer(kafka_url)

    # Create thread pool
    thread_pool = ThreadPool(monitor_interval=monitoring_interval)

    # Add tasks to thread pool
    thread_pool.add_task(name='monitor_traffic', target=monitor_traffic_task,
                         args=(docker_network_name, traffic_producer),
                         daemon=False)

    thread_pool.add_task(name='log_message_count', target=log_message_count_task,
                         args=(monitoring_interval,))

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, stop_threads_handler(
        thread_pool=thread_pool,
        traffic_producer=traffic_producer))

    # Start the threads
    thread_pool.start_threads()

    # Monitor threads
    thread_pool.monitor_threads()

    logger.info("Exiting...")
    sys.exit(0)


if __name__ == '__main__':
    main()
