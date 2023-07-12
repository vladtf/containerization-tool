import json
import logging
import os
import re
import signal
import subprocess
import sys
import threading
import time

import pyshark
from confluent_kafka import Producer

from configuration import config_loader
from kafka.kafka_client import create_kafka_producer

# Configure the logger
logging.basicConfig(level=logging.INFO, format='[%(levelname)s] - %(message)s')
logger = logging.getLogger("monitor-docker-traffic")

# Counter variable to keep track of the message count
message_count = 0

# Global variable to stop threads
# TODO: to replace with an thread pool
stop_threads = False


# Signal handler
def signal_handler(sig, frame):
    global stop_threads
    stop_threads = True
    logger.info("Interrupt signal received. Stopping threads...")


def get_docker_interface(docker_network_name):
    command = ['docker', 'network', 'ls',
               '--filter', f"name={docker_network_name}"]
    result = subprocess.run(command, capture_output=True, text=True)

    match = re.search(r"(\w{12})", result.stdout)
    if match:
        interface_id = match.group(1)
        return "br-" + interface_id

    logger.error("Error getting docker interface")
    exit(1)


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
    global stop_threads

    while not stop_threads:
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

    # Create threads
    threads = {
        'monitor_traffic': build_monitor_traffic_task(docker_network_name, traffic_producer),
        'log_message_count': build_log_message_count_task(monitoring_interval)
    }

    # Set up signal handler for Ctrl+C
    signal.signal(signal.SIGINT, signal_handler)

    # Start the threads
    for thread_name, thread in threads.items():
        logger.info("Starting thread '%s'...", thread_name)
        thread.start()

    try:
        while not stop_threads:
            for thread_name, thread in threads.items():
                if thread.is_alive():
                    continue

                logger.error("Thread '%s' is not alive. Restarting...", thread_name)

                if thread_name == 'monitor_traffic':
                    threads[thread_name] = build_monitor_traffic_task(docker_network_name, traffic_producer)

                elif thread_name == 'log_message_count':
                    threads[thread_name] = build_log_message_count_task(monitoring_interval)

                threads[thread_name].start()

            time.sleep(monitoring_interval)
    except KeyboardInterrupt:
        logger.info("Interrupted by user. Exiting...")

    finally:
        for thread_name, thread in threads.items():
            logger.info("Stopping thread '%s'...", thread_name)
            thread.join()

            # Close the Kafka producer
        traffic_producer.flush()

        logger.info("All threads stopped. Exiting...")

    logger.info("Exiting...")
    sys.exit(0)


def build_log_message_count_task(monitoring_interval: int):
    return threading.Thread(target=log_message_count_task, args=(monitoring_interval,))


def build_monitor_traffic_task(docker_network_name, traffic_producer):
    return threading.Thread(target=monitor_traffic_task,
                            args=(docker_network_name, traffic_producer))


if __name__ == '__main__':
    main()
