
LOG_FILE="logs/$(date +"%Y-%m-%d").log"

# Color codes
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[0;33m'
NC='\033[0m' # No Color

# Logging functions
log_success() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[SUCCESS] $1"
    echo -e "${GREEN}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_error() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[ERROR] $1"

    echo -e "${RED}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_warning() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[WARNING] $1"
    echo -e "${YELLOW}$timestamp - $log_message${NC}"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}

log_info() {
    local timestamp=$(date +"%Y-%m-%d %H:%M:%S")
    local log_message="[INFO] $1"
    echo -e "$timestamp - $log_message"
    echo -e "$timestamp - $log_message" >>"$LOG_FILE"
}
