import binascii
import pyshark
import subprocess
import re
import json
from confluent_kafka import Producer


def get_docker_interface(docker_network_name):
    # Run the "docker network ls" command
    command = ['docker', 'network', 'ls',
               '--filter', f"name={docker_network_name}"]
    result = subprocess.run(command, capture_output=True, text=True)

    # Get the id of the Docker network
    match = re.search(r"(\w{12})", result.stdout)

    if match:
        interface_id = match.group(1)
        return "br-" + interface_id

    return None


def kafka_producer(message):
    bootstrap_servers = 'localhost:29092'
    topic = 'monitor-docker-traffic'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()


def packet_callback(pkt):
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
    # print(json_message)
    
    kafka_producer(json_message)



# Docker network name
# docker_network_name = 'vta-ip-project_app_network'
docker_network_name = 'mynetwork'

# Get the Docker network interface name
interface = get_docker_interface(docker_network_name)

# Print the interface name
print("Docker network interface name: " + interface)

if interface:
    # Set up the packet capture
    capture = pyshark.LiveCapture(interface=interface)

    # Start capturing packets and invoke the packet_callback function for each packet
    capture.apply_on_packets(packet_callback)
else:
    print("Failed to retrieve Docker network interface name.")
