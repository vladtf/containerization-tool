import pyshark

def packet_callback(pkt):
    print(pkt)

# Specify the network interface to capture packets from
interface = "vta-ip-project_app_network"

# Set up the packet capture
capture = pyshark.LiveCapture(interface=interface)

# Start capturing packets and invoke the packet_callback function for each packet
capture.apply_on_packets(packet_callback)
