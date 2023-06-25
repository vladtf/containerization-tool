import binascii
import pyshark
import subprocess
import re

def get_docker_interface():
    # Run the "docker network inspect" command to get network information
    command = ['docker', 'network', 'inspect', 'vta-ip-project_app_network']
    result = subprocess.run(command, capture_output=True, text=True)

    # Extract the interface name from the command output using regular expressions
    match = re.search(r'"Name": "(.*?)",', result.stdout)
    if match:
        interface_name = match.group(1)
        return interface_name

    return None

def packet_callback(pkt):
    # print(pkt)

    if 'ip' in pkt:
        # Print the source and destination IP addresses
        print(f"{pkt.ip.src} -> {pkt.ip.dst} (ip)")

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

# Get the Docker network interface name
# interface = get_docker_interface()
interface = "br-518cfbfe4d4f"


# Print the interface name
print("Docker network interface name: " + interface)

if interface:
    # Set up the packet capture
    capture = pyshark.LiveCapture(interface=interface)

    # Start capturing packets and invoke the packet_callback function for each packet
    capture.apply_on_packets(packet_callback)
else:
    print("Failed to retrieve Docker network interface name.")
