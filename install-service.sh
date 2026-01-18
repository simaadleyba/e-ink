#!/bin/bash
# Installation script for Manul E-Ink Display service
# This script sets up safe power-cycling and hourly updates

echo "=== Manul E-Ink Display Service Installer ==="
echo ""

# Get the absolute path to the project directory
PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_DIR"
echo ""

# Create systemd service file
echo "Creating systemd service..."
sudo tee /etc/systemd/system/manul-display.service > /dev/null <<EOF
[Unit]
Description=Manul E-Ink Display
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/manul_display.py
WorkingDirectory=${PROJECT_DIR}
User=${USER}
StandardOutput=journal
StandardError=journal
# Safe shutdown handling
TimeoutStopSec=10
KillMode=mixed
# Restart on failure
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF

# Create hourly timer for map refreshes
echo "Creating hourly timer..."
sudo tee /etc/systemd/system/manul-hourly.service > /dev/null <<EOF
[Unit]
Description=Manul E-Ink Display Hourly Update
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/manul_display.py --refresh-map
WorkingDirectory=${PROJECT_DIR}
User=${USER}
StandardOutput=journal
StandardError=journal
EOF

sudo tee /etc/systemd/system/manul-hourly.timer > /dev/null <<EOF
[Unit]
Description=Manul E-Ink Display Hourly Timer
Requires=manul-hourly.service

[Timer]
# Run every hour
OnCalendar=hourly
# Run on boot if missed
Persistent=true
# Random delay to avoid API rate limiting
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF

# Reload systemd
echo "Reloading systemd..."
sudo systemctl daemon-reload

# Enable services
echo "Enabling services..."
sudo systemctl enable manul-display.service
sudo systemctl enable manul-hourly.timer

# Start timer
echo "Starting hourly timer..."
sudo systemctl start manul-hourly.timer

# Run once now
echo ""
echo "Running initial display update..."
sudo systemctl start manul-display.service

echo ""
echo "=== Installation Complete! ==="
echo ""
echo "The display will now:"
echo "  - Update on boot"
echo "  - Update every hour (new random city)"
echo "  - Handle power cycles safely"
echo ""
echo "Useful commands:"
echo "  Check status:     sudo systemctl status manul-display.service"
echo "  View logs:        journalctl -u manul-display.service -f"
echo "  Check timer:      sudo systemctl status manul-hourly.timer"
echo "  List next runs:   systemctl list-timers manul-hourly.timer"
echo "  Manual update:    sudo systemctl start manul-display.service"
echo "  Stop hourly:      sudo systemctl stop manul-hourly.timer"
echo "  Disable auto-run: sudo systemctl disable manul-display.service"
echo ""
