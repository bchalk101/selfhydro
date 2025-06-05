#!/bin/bash

# Colors for log formatting
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
BLUE='\033[0;34m'
NC='\033[0m' # No Color

# Default values
HOST="selfhydro.local"
USER="base"
SERVICE="selfhydro"

# Help message
show_help() {
    echo "Usage: $0 [OPTIONS]"
    echo "Monitor selfhydro logs over SSH"
    echo ""
    echo "Options:"
    echo "  -H, --host HOST      Remote host (default: selfhydro.local)"
    echo "  -u, --user USER      SSH user (default: base)"
    echo "  -s, --service NAME   Service name (default: selfhydro)"
    echo "  -h, --help          Show this help message"
}

# Parse command line arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -H|--host)
            HOST="$2"
            shift 2
            ;;
        -u|--user)
            USER="$2"
            shift 2
            ;;
        -s|--service)
            SERVICE="$2"
            shift 2
            ;;
        -h|--help)
            show_help
            exit 0
            ;;
        *)
            echo "Unknown option: $1"
            show_help
            exit 1
            ;;
    esac
done

# Function to colorize output
colorize() {
    while IFS= read -r line; do
        if [[ $line == *"ERROR"* ]] || [[ $line == *"FATAL"* ]]; then
            echo -e "${RED}${line}${NC}"
        elif [[ $line == *"WARN"* ]]; then
            echo -e "${YELLOW}${line}${NC}"
        elif [[ $line == *"INFO"* ]]; then
            echo -e "${GREEN}${line}${NC}"
        elif [[ $line == *"DEBUG"* ]]; then
            echo -e "${BLUE}${line}${NC}"
        else
            echo "$line"
        fi
    done
}

echo "=== Monitoring logs for ${SERVICE} service ==="
echo "Host: ${HOST}"
echo "User: ${USER}"
echo "Following logs in real-time (Ctrl+C to exit)"
echo "================================================"

# Execute SSH command and monitor logs
ssh -t "${USER}@${HOST}" "journalctl -u ${SERVICE} -f" | colorize 