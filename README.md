# E-Ink Dashboard (Raspberry Pi Zero)

A minimal, high-legibility e-ink dashboard for a Waveshare 7.5" display. The dashboard shows:

- Date & time (Europe/Istanbul)
- Apple Reminders (via CalDAV)
- Weather for Istanbul (Open-Meteo)

## Display

- Model: Waveshare 7.5" (800x480)
- Font: IBM Plex Mono

## Requirements

- Python 3.9+
- Waveshare e-ink Python driver (`waveshare-epd`)
- Dependencies from `requirements.txt`

## Configuration

Edit `config.yaml`:

```yaml
dashboard:
  timezone: Europe/Istanbul

reminders:
  method: caldav
  username: "<apple_id_email>"
  app_password: "<app_specific_password>"
  caldav_url: "<full CalDAV base or principal URL>"
  list_name: "Reminders"
  max_items: 8
  show_completed: false

weather:
  latitude: 41.0082
  longitude: 28.9784
  timezone: Europe/Istanbul

text:
  font_path: "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf"
```

## Running

Test mode (renders `dashboard_preview.png` without touching the display):

```bash
python3 dashboard.py --test-mode
```

Run on device:

```bash
python3 dashboard.py
```

## Systemd service

Use `install-service.sh` to install the dashboard service and hourly refresh timer.

```bash
./install-service.sh
```

## Notes

If you don't have IBM Plex Mono installed, the app falls back to DejaVu Sans Mono.
