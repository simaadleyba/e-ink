#!/bin/bash
# Install systemd units for the e-ink dashboard.

set -euo pipefail

PROJECT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
SERVICE_NAME="eink-dashboard"
PYTHON_BIN="$(command -v python3)"
RUN_USER="${SUDO_USER:-$USER}"

if [[ -z "${PYTHON_BIN}" ]]; then
  echo "python3 not found in PATH"
  exit 1
fi

cat <<EOF | sudo tee "/etc/systemd/system/${SERVICE_NAME}.service" >/dev/null
[Unit]
Description=E-Ink Dashboard Refresh
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
WorkingDirectory=${PROJECT_DIR}
ExecStart=${PYTHON_BIN} ${PROJECT_DIR}/dashboard.py --config ${PROJECT_DIR}/config.yaml
User=${RUN_USER}
StandardOutput=journal
StandardError=journal
EOF

cat <<EOF | sudo tee "/etc/systemd/system/${SERVICE_NAME}.timer" >/dev/null
[Unit]
Description=Run E-Ink Dashboard hourly

[Timer]
OnBootSec=2min
OnUnitActiveSec=1h
Persistent=true
RandomizedDelaySec=2min
Unit=${SERVICE_NAME}.service

[Install]
WantedBy=timers.target
EOF

sudo systemctl daemon-reload
sudo systemctl enable "${SERVICE_NAME}.timer"
sudo systemctl start "${SERVICE_NAME}.timer"
sudo systemctl start "${SERVICE_NAME}.service"

echo "Installed ${SERVICE_NAME}.service and ${SERVICE_NAME}.timer"
echo "Status: sudo systemctl status ${SERVICE_NAME}.service"
echo "Timer:  sudo systemctl status ${SERVICE_NAME}.timer"
