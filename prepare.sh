#!/bin/bash

# flag to indicate this script was sourced
export PREPARE_SH_SOURCED=true

# save current directory
BIN_DIR=$(dirname $0)

# declare alias to connect to test container
alias go-test='docker exec -it my-ubuntu bash'

# source python virtual environment
source $BIN_DIR/utils/myenv/bin/activate