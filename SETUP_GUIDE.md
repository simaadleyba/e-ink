# E-Ink Dashboard Setup Guide (Waveshare 7.5")

This is the only setup doc you need for this project.

## What this dashboard renders

- Left sidebar: high-zoom Stadia Stamen map centered on your configured coordinates
- Main area:
  - large local time
  - Hong Kong and Boston times
  - daily rotating motivational quote from a local JSON file

The design is pure black/white for e-ink readability.

## 1) Connect to Raspberry Pi over SSH

From your laptop:

```bash
ssh pi@<raspberry-pi-ip>
```

Find your Pi IP (if needed):

```bash
hostname -I
```

If SSH is disabled, enable it once from Raspberry Pi OS:

```bash
sudo raspi-config
# Interface Options -> SSH -> Enable
```

## 2) Clone project and install dependencies

```bash
git clone <your-repo-url> e-ink
cd e-ink
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 3) Install fonts (IBM Plex Mono preferred)

```bash
sudo apt update
sudo apt install -y fonts-ibm-plex fonts-dejavu-core
```

Optional fallback if you manually install Google Sans Mono:

- Place `GoogleSansMono-Regular.ttf` in a system font directory.
- Keep the configured fallback order in `config.yaml`.

## 4) Wire Waveshare 7.5" HAT to Raspberry Pi (SPI)

Use the official Waveshare wiring for your specific 7.5" HAT revision.

Common SPI signals:

- `VCC` -> `3.3V`
- `GND` -> `GND`
- `DIN` -> `MOSI` (GPIO10)
- `CLK` -> `SCLK` (GPIO11)
- `CS` -> `CE0` (GPIO8)
- `DC` -> GPIO pin defined by Waveshare library
- `RST` -> GPIO pin defined by Waveshare library
- `BUSY` -> GPIO pin defined by Waveshare library

Enable SPI:

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
sudo reboot
```

## 5) Configure dashboard

Edit `config.yaml`:

```yaml
timezones:
  local: America/Los_Angeles
  hong_kong: Asia/Hong_Kong
  boston: America/New_York

map:
  latitude: 37.7749
  longitude: -122.4194
  location_label: San Francisco
  zoom: 14
  render_scale: 2
  tile_url_template: https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png
  api_key: null
```

Recommended map quality settings for 800x480 e-ink:

- `zoom: 14`
- `render_scale: 2`

## 6) API / external service requirements

- Map tiles: Stadia Maps (`stamen_toner` style)
  - API key: optional in config (`map.api_key`) but recommended for reliability and quota control
  - Sign up and create a key at [Stadia Maps](https://stadiamaps.com/)
- Quotes: local file `eink_dashboard/assets/quotes.json`
  - No API key needed

## 7) Preview on laptop before deploying

From project root:

```bash
python3 dashboard.py --preview
```

Output PNG:

- `preview/dashboard_preview.png`

Custom path:

```bash
python3 dashboard.py --preview --output /tmp/eink-preview.png
```

## 8) Run once on the display

```bash
python3 dashboard.py
```

## 9) Auto-refresh with systemd (recommended)

Install units:

```bash
./install-service.sh
```

Check status:

```bash
sudo systemctl status eink-dashboard.service
sudo systemctl status eink-dashboard.timer
journalctl -u eink-dashboard.service -f
```

## 10) Cron fallback (optional)

If you prefer cron instead of systemd:

```bash
crontab -e
```

Add:

```cron
@reboot cd /path/to/e-ink && /usr/bin/python3 dashboard.py --config config.yaml
0 * * * * cd /path/to/e-ink && /usr/bin/python3 dashboard.py --config config.yaml
```

## 11) Troubleshooting

- `ModuleNotFoundError: waveshare_epd`
  - Install Waveshare Python library compatible with your HAT revision.
- Font fallback is used unexpectedly
  - Confirm IBM Plex Mono path exists on Pi.
- Map area shows crossed placeholder tiles
  - Check network, tile URL template, and optional Stadia API key.
