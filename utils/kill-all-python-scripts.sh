#!/bin/sh

# Kill all python scripts
kill_python_script(){
    script_name=$1
    for pid in $(ps aux | grep "$script_name" | grep -v grep | awk '{print $2}'); do
        log_info "Stopping monitoring (PID: $pid)"
        kill "$pid"
    done
}

kill_python_script "containers-manager.py"
kill_python_script "monitor-docker-traffic.py"
kill_python_script "monitor-forwarding-rules.py"

# List all python scripts
ps aux | grep python
