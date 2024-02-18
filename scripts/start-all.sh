#!/bin/bash
BIN_DIR=$(dirname $0)
SCRIPTS_DIR=$BIN_DIR/scripts

# Create a new tmux session and give it a name
tmux new-session -d -s monitoring-session

# Start the first script in the first pane
tmux send-keys -t monitoring-session "${SCRIPTS_DIR}/start-containers-manager.sh" C-m

# Split the window horizontally, creating two vertical panes
tmux split-window -h

# Start the second script in the new pane
tmux send-keys -t monitoring-session "${SCRIPTS_DIR}/start-monitoring-forwarding-rules.sh" C-m

# Select the first pane and split it vertically, creating two horizontal panes
tmux select-pane -L
tmux split-window -v

# Start the third script in the new pane
tmux send-keys -t monitoring-session "${SCRIPTS_DIR}/start-monitoring-traffic.sh" C-m

# Select the second pane (on the right side) and split it vertically, creating two horizontal panes
tmux select-pane -R
tmux split-window -v

# Set layout to even-horizontal to distribute space between all panes equally
tmux select-layout -t monitoring-session tiled

# Set pane synchronization to on
tmux set-window-option -t monitoring-session synchronize-panes on

# Attach to the tmux session to view the logs
tmux attach-session -t monitoring-session


# TODO: stop the entire session when one of the scripts exits