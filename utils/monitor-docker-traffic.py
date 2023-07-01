import binascii
import pyshark
import subprocess
import re
from confluent_kafka import Producer


def get_docker_interface(docker_network_name):
    # Run the "docker network ls" command
    command = ['docker', 'network', 'ls', '--filter', f"name={docker_network_name}"]
    result = subprocess.run(command, capture_output=True, text=True)


    # Get the id of the Docker network
    match = re.search(r"(\w{12})", result.stdout)
    
    if match:
        interface_id = match.group(1)
        return "br-" + interface_id

    return None

def kakfa_producer(message):
    bootstrap_servers = 'localhost:29092'
    topic = 'monitor-docker-traffic'

    producer = Producer({'bootstrap.servers': bootstrap_servers})

    producer.produce(topic, key='my_key', value=message)

    producer.flush()

def packet_callback(pkt):
    # print(pkt)

    if 'ip' in pkt:
        # Print the source and destination IP addresses
        print(f"{pkt.ip.src} -> {pkt.ip.dst} (ip)")
        kakfa_producer(f"{pkt.ip.src} -> {pkt.ip.dst} (ip)")

        # If the packet contains HTTP information, print the request and response
        # if 'http' in pkt:
        #     packet_bytes = binascii.unhexlify(pkt.eth.raw_mode.replace(':', ''))
        #     print(f"Packet Bytes: {packet_bytes}")
        
    elif 'ipv6' in pkt:
        print(f"{pkt.ipv6.src} -> {pkt.ipv6.dst} (ipv6)")
    elif 'arp' in pkt:
        print(f"{pkt.arp.src_hw_mac} -> {pkt.arp.dst_hw_mac} (arp)")
    elif 'tcp' in pkt:
        print(f"{pkt.tcp.srcport} -> {pkt.tcp.dstport} (tcp)")
    elif 'udp' in pkt:
        print(f"{pkt.udp.srcport} -> {pkt.udp.dstport} (udp)")
    elif 'icmp' in pkt:
        print(f"{pkt.icmp.src} -> {pkt.icmp.dst} (icmp)")
    else:
        print("Unknown packet type")

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
