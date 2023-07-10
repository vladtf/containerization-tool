#!/bin/sh


# Kill all python scripts
pkill -f "python3 ./monitoring/containers-manager.py"
pkill -f "python3 ./monitoring/monitor-docker-traffic.py"
pkill -f "python3 ./monitoring/monitor-forwarding-rules.py"

# List all python scripts
ps aux | grep python
