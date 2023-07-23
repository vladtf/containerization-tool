#!/usr/bin/env python3


import socket
import time

def ping_google_dns():
    target_host = "8.8.8.8"
    target_port = 53
    timeout = 2  # Timeout in seconds

    try:
        # Create a socket object
        client_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)

        # Set a timeout for the socket connection
        client_socket.settimeout(timeout)

        # Connect to the Google DNS server
        client_socket.connect((target_host, target_port))

        print("Ping to Google DNS (8.8.8.8) successful!")
    except socket.error as e:
        print("Ping to Google DNS (8.8.8.8) failed:", e)
    finally:
        # Close the socket
        client_socket.close()

if __name__ == "__main__":
    while True:
        ping_google_dns()
        time.sleep(3)  # Wait for 3 seconds before pinging again
