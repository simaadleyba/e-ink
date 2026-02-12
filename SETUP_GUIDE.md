# E-Ink Dashboard Setup Guide (Waveshare 7.5")

This project renders an 800x480 black/white dashboard:

- Left panel (160px): local 12-hour time, date, Hong Kong/Boston/Seattle clocks, quote
- Right panel (640px): Stadia Stamen Toner map, center pin, city + coordinates card

## 1) SSH into your Raspberry Pi

```bash
ssh pi@<raspberry-pi-ip>
```

If SSH is disabled:

```bash
sudo raspi-config
# Interface Options -> SSH -> Enable
```

## 2) Install system dependencies

```bash
sudo apt update
sudo apt install -y python3 python3-pip python3-venv git fonts-ibm-plex fonts-dejavu-core
```

## 3) Clone and install Python dependencies

```bash
git clone <your-repo-url> e-ink
cd e-ink
python3 -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -r requirements.txt
```

## 4) Waveshare wiring + SPI

Wire the 7.5" HAT to Raspberry Pi SPI using your HAT revision pinout.

Typical lines:

- `VCC` -> `3.3V`
- `GND` -> `GND`
- `DIN` -> `MOSI` (GPIO10)
- `CLK` -> `SCLK` (GPIO11)
- `CS` -> `CE0` (GPIO8)
- `DC`, `RST`, `BUSY` -> the GPIO pins expected by your Waveshare Python driver

Enable SPI:

```bash
sudo raspi-config
# Interface Options -> SPI -> Enable
sudo reboot
```

## 5) Configure `config.yaml`

Defaults already match your requested timezones:

- Local: `Europe/Istanbul`
- World clocks: `Asia/Hong_Kong`, `America/New_York`, `America/Los_Angeles`

Map defaults:

- Stadia Stamen Toner
- zoom `15`
- render scale `2`
- location `40.89, 29.38` (Istanbul)

## 6) API key requirement (Stadia Maps)

- You can run without a key in some environments.
- For reliable production usage, you should use a Stadia API key.
- Set it in `config.yaml`:

```yaml
map:
  api_key: "<your_stadia_api_key>"
```

## 7) Preview on laptop/Pi

```bash
python3 dashboard.py --preview
```

Preview output:

- `preview/dashboard_preview.png`

## 8) Run once on display

```bash
python3 dashboard.py
```

## 9) Enable auto-refresh (systemd)

```bash
./install-service.sh
```

Check:

```bash
sudo systemctl status eink-dashboard.service
sudo systemctl status eink-dashboard.timer
journalctl -u eink-dashboard.service -f
```

## 10) Optional cron fallback

```bash
crontab -e
```

Add:

```cron
@reboot cd /path/to/e-ink && /usr/bin/python3 dashboard.py --config config.yaml
0 * * * * cd /path/to/e-ink && /usr/bin/python3 dashboard.py --config config.yaml
```
