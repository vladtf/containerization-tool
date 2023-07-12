FROM ubuntu:latest

# Install basic tools
RUN apt-get update && \
    apt-get install -y iptables iproute2 iputils-ping net-tools tcpdump \
    vim git curl wget && \
    apt-get clean && \
    rm -rf /var/lib/apt/lists/*

# Copy iptables rules file
# COPY iptables-rules /root/iptables-rules

# Apply the predefined iptables rules
# RUN iptables-restore < /root/iptables-rules

CMD ["tail", "-f", "/dev/null"]

