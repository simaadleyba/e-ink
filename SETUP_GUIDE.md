# Setup Guide

## Overview

This dashboard renders a minimal e-ink layout with the current time, Apple Reminders, and Istanbul weather.

## Install

```bash
python3 -m pip install -r requirements.txt
```

## Configure

Edit `config.yaml` and set your Apple ID CalDAV credentials:

```yaml
reminders:
  method: caldav
  username: "<apple_id_email>"
  app_password: "<app_specific_password>"
  caldav_url: "<full CalDAV base or principal URL>"
  list_name: "Reminders"
  max_items: 8
  show_completed: false
```

## Test render

```bash
python3 dashboard.py --test-mode
```

The output image is saved as `dashboard_preview.png`.

## Run on device

```bash
python3 dashboard.py
```

## Systemd service

```bash
./install-service.sh
```

This installs `dashboard.service` and `dashboard-hourly.timer` for hourly refreshes.
