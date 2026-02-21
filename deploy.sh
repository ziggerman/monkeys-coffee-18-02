#!/bin/bash

# Monkeys Coffee Bot - Deployment Script for VPS
# Run as: sudo bash deploy.sh

set -e

echo "🚀 Monkeys Coffee Bot - Deployment Script"
echo "=========================================="

# Colors
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if running as root
if [ "$EUID" -ne 0 ]; then
    echo -e "${YELLOW}Please run as root or with sudo${NC}"
    exit 1
fi

# Get current directory (where script is run from)
CURRENT_DIR="$( cd "$( dirname "${BASH_SOURCE[0]}" )" && pwd )"

# Variables
APP_DIR="/opt/monkeys-coffee"
SERVICE_NAME="monkeys-bot"
VENV_DIR="$APP_DIR/venv"

echo -e "${GREEN}Current directory: $CURRENT_DIR${NC}"
echo -e "${GREEN}Target directory: $APP_DIR${NC}"

# 1. Create application directory
echo -e "${GREEN}1. Creating application directory...${NC}"
mkdir -p $APP_DIR

# 2. Copy application files
echo -e "${GREEN}2. Copying application files...${NC}"
# Copy all files except .env, venv, __pycache__, *.db, *.log
rsync -av --exclude='.env' --exclude='venv' --exclude='__pycache__' --exclude='*.db' --exclude='*.log' --exclude='.git' --exclude='node_modules' --exclude='.DS_Store' $CURRENT_DIR/ $APP_DIR/

# 3. Set up Python virtual environment
echo -e "${GREEN}3. Setting up Python virtual environment...${NC}"
cd $APP_DIR

# Create venv if it doesn't exist
if [ ! -d "$VENV_DIR" ]; then
    echo "Creating new virtual environment..."
    python3 -m venv $VENV_DIR
fi

source $VENV_DIR/bin/activate
pip install --upgrade pip
pip install -r requirements.txt
deactivate

# 4. Create .env file if not exists
echo -e "${GREEN}4. Setting up environment variables...${NC}"
if [ ! -f "$APP_DIR/.env" ]; then
    echo -e "${YELLOW}WARNING: .env file not found!${NC}"
    echo "Please create $APP_DIR/.env with your configuration"
    echo "See .env.production.example for reference"
fi

# 5. Initialize database if needed
echo -e "${GREEN}5. Setting up database...${NC}"
if [ ! -f "$APP_DIR/db_store/monkeys_coffee.db" ]; then
    echo "Database not found, initializing..."
    cd $APP_DIR
    source $VENV_DIR/bin/activate
    python3 -c "from src.database.session import init_db; import asyncio; asyncio.run(init_db())"
    deactivate
    echo -e "${GREEN}Database initialized!${NC}"
else
    echo -e "${GREEN}Database already exists, skipping...${NC}"
fi

# 6. Install and configure systemd service
echo -e "${GREEN}6. Installing systemd service...${NC}"
cp $APP_DIR/monkeys-bot.service /etc/systemd/system/$SERVICE_NAME.service
systemctl daemon-reload
systemctl enable $SERVICE_NAME

# 7. Start the bot
echo -e "${GREEN}7. Starting the bot...${NC}"
systemctl start $SERVICE_NAME
sleep 3

# 8. Check status
echo -e "${GREEN}8. Checking bot status...${NC}"
systemctl status $SERVICE_NAME --no-pager

# 9. Show logs
echo -e "${GREEN} Bot logs:${NC}"
journalctl -u $SERVICE_NAME -n 20 --no-pager

echo ""
echo -e "${GREEN}✅ Deployment complete!${NC}"
echo ""
echo "Useful commands:"
echo "  systemctl status $SERVICE_NAME   - Check status"
echo "  journalctl -u $SERVICE_NAME -f  - View logs"
echo "  systemctl restart $SERVICE_NAME  - Restart bot"
echo ""
echo "To update database with new data, run:"
echo "  cd $APP_DIR"
echo "  source venv/bin/activate"
echo "  python3 load_demo_data.py"
echo "  deactivate"
