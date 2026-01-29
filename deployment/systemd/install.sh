#!/bin/bash
# ANPR System Installation Script

set -e

echo "Installing ANPR System..."

# Create user
sudo useradd -r -s /bin/false -m -d /opt/anpr anpr || true

# Create directories
sudo mkdir -p /opt/anpr
sudo mkdir -p /var/log/anpr

# Copy files (assumes running from project root)
sudo cp -r . /opt/anpr/

# Set permissions
sudo chown -R anpr:anpr /opt/anpr /var/log/anpr

# Install dependencies
cd /opt/anpr
sudo -u anpr python3 -m venv venv
sudo -u anpr /opt/anpr/venv/bin/pip install -r requirements.txt

# Install systemd service
sudo cp deployment/systemd/anpr.service /etc/systemd/system/
sudo systemctl daemon-reload
sudo systemctl enable anpr.service

echo "Installation complete!"
echo "Start: sudo systemctl start anpr"
echo "Status: sudo systemctl status anpr"