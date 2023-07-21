#!/bin/sh

# Kill all python scripts
pkill -f "containers-manager.py"
pkill -f "monitor-docker-traffic.py"
pkill -f "monitor-forwarding-rules.py"

# List all python scripts
ps aux | grep python
