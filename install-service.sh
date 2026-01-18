#!/bin/bash
# Installation script for the E-Ink Dashboard service

set -e

echo "=== E-Ink Dashboard Service Installer ==="
echo ""

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
echo "Project directory: $PROJECT_DIR"
echo ""

# Create systemd service file
printf "%s\n" "Creating systemd service..."
sudo tee /etc/systemd/system/dashboard.service > /dev/null <<EOF_SERVICE
[Unit]
Description=E-Ink Dashboard
After=network-online.target
Wants=network-online.target
StartLimitIntervalSec=0

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/dashboard.py
WorkingDirectory=${PROJECT_DIR}
User=${USER}
StandardOutput=journal
StandardError=journal
TimeoutStopSec=10
KillMode=mixed
Restart=on-failure
RestartSec=30

[Install]
WantedBy=multi-user.target
EOF_SERVICE

# Create hourly refresh timer
printf "%s\n" "Creating hourly timer..."
sudo tee /etc/systemd/system/dashboard-hourly.service > /dev/null <<EOF_HOURLY
[Unit]
Description=E-Ink Dashboard Hourly Update
After=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 ${PROJECT_DIR}/dashboard.py
WorkingDirectory=${PROJECT_DIR}
User=${USER}
StandardOutput=journal
StandardError=journal
EOF_HOURLY

sudo tee /etc/systemd/system/dashboard-hourly.timer > /dev/null <<EOF_TIMER
[Unit]
Description=E-Ink Dashboard Hourly Timer
Requires=dashboard-hourly.service

[Timer]
OnCalendar=hourly
Persistent=true
RandomizedDelaySec=300

[Install]
WantedBy=timers.target
EOF_TIMER

printf "%s\n" "Reloading systemd..."
sudo systemctl daemon-reload

printf "%s\n" "Enabling services..."
sudo systemctl enable dashboard.service
sudo systemctl enable dashboard-hourly.timer

printf "%s\n" "Starting hourly timer..."
sudo systemctl start dashboard-hourly.timer

printf "%s\n" ""
printf "%s\n" "Running initial dashboard update..."
sudo systemctl start dashboard.service

printf "%s\n" ""
printf "%s\n" "=== Installation Complete! ==="
printf "%s\n" ""
printf "%s\n" "The display will now:"
printf "%s\n" "  - Update on boot"
printf "%s\n" "  - Update every hour"
printf "%s\n" "  - Handle power cycles safely"
printf "%s\n" ""
printf "%s\n" "Useful commands:"
printf "%s\n" "  Check status:     sudo systemctl status dashboard.service"
printf "%s\n" "  View logs:        journalctl -u dashboard.service -f"
printf "%s\n" "  Check timer:      sudo systemctl status dashboard-hourly.timer"
printf "%s\n" "  List next runs:   systemctl list-timers dashboard-hourly.timer"
printf "%s\n" "  Manual update:    sudo systemctl start dashboard.service"
printf "%s\n" "  Stop hourly:      sudo systemctl stop dashboard-hourly.timer"
printf "%s\n" "  Disable auto-run: sudo systemctl disable dashboard.service"
printf "%s\n" ""
