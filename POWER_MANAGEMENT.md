# Power Management & Systemd

## Services

- `dashboard.service` — runs the dashboard once
- `dashboard-hourly.timer` — hourly refresh

## Useful commands

```bash
sudo systemctl status dashboard.service
sudo systemctl start dashboard.service
sudo systemctl status dashboard-hourly.timer
sudo systemctl start dashboard-hourly.timer
journalctl -u dashboard.service -f
```

## Install

```bash
./install-service.sh
```
