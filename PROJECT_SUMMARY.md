# Project Summary

A Raspberry Pi Zero e-ink dashboard for a Waveshare 7.5" display (800x480).

## Features

- Date & time header (Europe/Istanbul)
- Apple Reminders via CalDAV
- Weather for Istanbul (Open-Meteo)
- Minimal, high-legibility layout using IBM Plex Mono

## Entry point

- `dashboard.py` — main script

## Core modules

- `reminders_provider.py` — CalDAV integration for Apple Reminders
- `weather_provider.py` — Open-Meteo weather fetch
- `render_utils.py` — text wrapping and layout helpers

## Configuration

Update `config.yaml` with:

- CalDAV credentials (Apple ID + app-specific password)
- Istanbul timezone and coordinates
- Display model and font settings

## Service

Use `install-service.sh` to install the systemd service and hourly refresh timer.
