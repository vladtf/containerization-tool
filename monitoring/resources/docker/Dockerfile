FROM ubuntu:latest

# Install basic tools
RUN apt-get update && \
    apt-get install -y iptables iproute2 iputils-ping net-tools tcpdump \
    vim git curl wget netcat traceroute dnsutils && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

COPY ./entrypoint.bin /usr/local/bin/entrypoint.bin
RUN chmod +x /usr/local/bin/entrypoint.bin

CMD ["/usr/local/bin/entrypoint.bin"]
