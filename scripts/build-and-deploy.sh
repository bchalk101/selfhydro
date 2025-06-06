#!/bin/bash

# Exit on error
set -e

# Colors for output
GREEN='\033[0;32m'
RED='\033[0;31m'
YELLOW='\033[1;33m'
NC='\033[0m'

# Configuration
PI_HOST="base@selfhydro.local"
TARGET_DIR="/home/base/selfhydro"
SERVICE_NAME="selfhydro"

echo -e "${GREEN}Starting build and deploy process on Raspberry Pi...${NC}"

# Step 1: Install dependencies
echo -e "\n${YELLOW}Installing required dependencies...${NC}"
ssh $PI_HOST "sudo apt-get update && sudo apt-get install -y libssl-dev pkg-config i2c-tools"

# Step 2: Create directories on Pi
echo -e "\n${YELLOW}Creating deployment directories...${NC}"
ssh $PI_HOST "mkdir -p $TARGET_DIR/bin"

# Step 3: Copy source code to Pi
echo -e "\n${YELLOW}Copying source code to Raspberry Pi...${NC}"
rsync -av --exclude 'target' --exclude '.git' --exclude 'frontend' --exclude 'api_service' ./ $PI_HOST:$TARGET_DIR/

# Step 4: Run tests
echo -e "\n${YELLOW}Running tests on Raspberry Pi...${NC}"
ssh $PI_HOST "source ~/.bashrc && source ~/.profile && source \$HOME/.cargo/env && cd $TARGET_DIR && cargo test --workspace"

# Step 5: Build on Raspberry Pi
echo -e "\n${YELLOW}Building on Raspberry Pi...${NC}"
ssh $PI_HOST "source ~/.bashrc && source ~/.profile && source \$HOME/.cargo/env && cd $TARGET_DIR && cargo build --release --workspace"

# Step 6: Stop the service first
echo -e "\n${YELLOW}Stopping service...${NC}"
ssh $PI_HOST "sudo systemctl stop $SERVICE_NAME || true"

# Step 7: Copy binary to bin directory
echo -e "\n${YELLOW}Installing binary...${NC}"
ssh $PI_HOST "cp $TARGET_DIR/target/aarch64-unknown-linux-gnu/release/selfhydro-monitor $TARGET_DIR/bin/"

# Step 8: Setup service files
echo -e "\n${YELLOW}Setting up service...${NC}"
ssh $PI_HOST "sudo cp $TARGET_DIR/deploy/selfhydro.service /etc/systemd/system/"

# Step 9: Start service
echo -e "\n${YELLOW}Starting service...${NC}"
ssh $PI_HOST "sudo systemctl daemon-reload && \
              sudo systemctl enable $SERVICE_NAME && \
              sudo systemctl start $SERVICE_NAME"

echo -e "\n${GREEN}Deployment complete! Checking service status...${NC}"
ssh $PI_HOST "sudo systemctl status $SERVICE_NAME --no-pager"

echo -e "\nTo monitor logs, run: ${YELLOW}./scripts/monitor_logs.sh -H selfhydro.local${NC}"