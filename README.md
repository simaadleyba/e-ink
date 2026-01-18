# Manul E-Ink Display

A Raspberry Pi project that displays a static map and rotating manul (Pallas's cat) photos on a Waveshare 7.5" e-ink display.

## Features

- **70% Map Panel**: Displays high-contrast monochrome maps from Stadia Maps (Stamen Toner style)
- **Random City Rotation**: Automatically rotates through 50+ major cities from Asia, North America, and Oceania
- **30% Sidebar**: Shows rotating e-inkified manul photos with metadata (name, location, description)
- **Smart Caching**: Minimizes API calls by caching maps and images locally
- **Offline Fallback**: Falls back to local manul storage when web scraping fails
- **E-Ink Optimized**: Contrast enhancement, quantization, and dithering for optimal e-ink display
- **Test Mode**: Develop and test without physical e-ink hardware

## Hardware Requirements

- Raspberry Pi (3/4/5 or Zero 2 W recommended)
- Waveshare 7.5" e-ink display (800x480, black & white)
- SD card (for storage)
- Power supply

## Software Requirements

- Python 3.7+
- Internet connection (for initial setup and map/manul fetching)

## Installation

### 1. Clone or Download

Download this project to your Raspberry Pi:

```bash
cd ~/Desktop/personal/e-ink
```

### 2. Install Dependencies

```bash
pip3 install -r requirements.txt
```

### 3. Configure

Edit `config.yaml` and add your Stadia Maps API key:

```yaml
stadia_maps:
  api_key: "YOUR_API_KEY_HERE"  # Get free key from https://stadiamaps.com/
```

You can also customize:
- Map center coordinates (default: Mongolia, manul habitat)
- Map zoom level
- Refresh intervals
- Contrast boost settings
- Display model (if not using epd7in5_V2)

### 4. Get Stadia Maps API Key

1. Go to https://stadiamaps.com/
2. Sign up for a free account
3. Create an API key
4. Copy it to `config.yaml`

The free tier includes 20,000 map requests per month, which is more than enough for this project.

## Usage

### Test Mode (No Hardware Required)

Test the system without e-ink hardware - saves output to `test_output.png`:

```bash
python3 manul_display.py --test-mode
```

### Full Refresh (Map + Manul)

Display a fresh map and new manul:

```bash
python3 manul_display.py
```

### Rotate Manul Only

Keep the current map, show a new manul:

```bash
python3 manul_display.py --rotate-manul
```

### Force Map Refresh

Force fetch new map from API (ignore cache):

```bash
python3 manul_display.py --refresh-map
```

### Test Individual Modules

Test map fetching:
```bash
python3 map_fetcher.py
```

Test manul scraping:
```bash
python3 manul_scraper.py
```

Test image processing:
```bash
python3 manul_processor.py
```

## Project Structure

```
e-ink/
├── manul_display.py         # Main orchestration script
├── map_fetcher.py            # Stadia Maps API client
├── manul_scraper.py          # Manulization.com web scraper
├── manul_processor.py        # Image e-inkification pipeline
├── config.yaml               # Configuration file
├── requirements.txt          # Python dependencies
├── cache/                    # Cached maps & images
│   ├── maps/
│   └── manuls/
├── local_manuls/             # Local manul storage (fallback)
│   ├── metadata.json
│   └── *.jpg                 # Add your own manul photos here
└── README.md                 # This file
```

## Local Manul Storage (Optional)

To add your own manul photos for offline use:

1. Add manul photos to `local_manuls/` directory
2. Edit `local_manuls/metadata.json`:

```json
[
  {
    "name": "Your Manul Name",
    "location": "Location",
    "description": "A description of this manul",
    "image_file": "your_manul.jpg"
  }
]
```

The system will automatically fall back to local manuls if web scraping fails.

## Automation

### Auto-start on Boot (systemd)

Create a systemd service to run on boot:

1. Create service file:
```bash
sudo nano /etc/systemd/system/manul-display.service
```

2. Add the following:
```ini
[Unit]
Description=Manul E-Ink Display
After=network.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pi/Desktop/personal/e-ink/manul_display.py
WorkingDirectory=/home/pi/Desktop/personal/e-ink
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

3. Enable and start:
```bash
sudo systemctl enable manul-display.service
sudo systemctl start manul-display.service
```

### Scheduled Updates (cron)

For periodic updates, add to crontab:

```bash
crontab -e
```

Add these lines:

```cron
# Refresh manul every 6 hours
0 */6 * * * cd /home/pi/Desktop/personal/e-ink && /usr/bin/python3 manul_display.py --rotate-manul >> /home/pi/manul.log 2>&1

# Refresh map daily at 6 AM
0 6 * * * cd /home/pi/Desktop/personal/e-ink && /usr/bin/python3 manul_display.py --refresh-map >> /home/pi/manul.log 2>&1
```

## Configuration Reference

### Display Settings

- `display.width/height`: E-ink display resolution (default: 800x480)
- `display.model`: Waveshare model (default: epd7in5_V2)

### Map Settings

- `map.random_city`: Enable random city selection from cities.yaml (default: true)
- `map.center_lat/lon`: Map center coordinates (used when random_city is false)
- `map.zoom`: Zoom level (1-20, higher = more zoomed in, 12 recommended for cities)
- `map.refresh_interval_hours`: How often to fetch new map (default: 24)
- `map.cities_file`: Path to cities YAML file (default: cities.yaml)

**City Maps**: The system includes 50+ major cities. See `CITY_MAPS.md` for details and customization.

### Image Processing

- `image_processing.contrast_boost`: Contrast multiplier (1.0-3.0, default: 2.2)
- `image_processing.use_clahe`: Use CLAHE instead of simple contrast (default: false)
- `image_processing.dithering`: Enable Floyd-Steinberg dithering (default: true)
- `image_processing.palette_colors`: Color palette size (default: 4)

### Tuning for Your Display

E-ink displays vary. If images look too dark/light:

1. Adjust `contrast_boost` in `config.yaml` (try 2.0 - 2.5)
2. Try enabling CLAHE: `use_clahe: true`
3. Test with `--test-mode` before updating actual display

## Troubleshooting

### "Failed to initialize e-ink display"

- Check that the Waveshare display is properly connected
- Verify the display model in `config.yaml` matches your hardware
- Ensure SPI is enabled: `sudo raspi-config` → Interface Options → SPI

### "Failed to fetch map from API"

- Check your Stadia Maps API key in `config.yaml`
- Verify internet connection
- Check API quota at https://stadiamaps.com/dashboard

### "Failed to fetch manul"

- Web scraping may have failed (site structure changed)
- Add local manul photos to `local_manuls/` as fallback
- Check internet connection

### Images look muddy on e-ink

- Increase `contrast_boost` in `config.yaml` (try 2.5 or 3.0)
- Enable CLAHE: `use_clahe: true`
- Test different values with `--test-mode`

### Module import errors

Make sure all dependencies are installed:
```bash
pip3 install -r requirements.txt
```

## Development

### Test Mode

Always test changes in test mode first:

```bash
python3 manul_display.py --test-mode
```

This saves output to `test_output.png` without touching the e-ink display.

### Logging

Set log level in `config.yaml`:

```yaml
logging:
  level: "DEBUG"  # DEBUG, INFO, WARNING, ERROR
```

### Adding Features

The modular architecture makes it easy to extend:

- **New map sources**: Modify `map_fetcher.py`
- **Different image sources**: Modify `manul_scraper.py`
- **Custom processing**: Modify `manul_processor.py`
- **Layout changes**: Modify `manul_display.py::_compose_layout()`

## Credits

- Maps: [Stadia Maps](https://stadiamaps.com/) (Stamen Toner style)
- Manul photos: [Manulization.com](https://manulization.com/)
- E-ink driver: [Waveshare](https://www.waveshare.com/)

## License

This project is provided as-is for personal use. Please respect the terms of service for Stadia Maps and Manulization.com when using this software.

## Fun Fact

Manuls (Pallas's cats) are small wild cats native to Central Asia. They have the longest and densest fur of all cats, which helps them survive in cold, rocky habitats. Despite their cute appearance, they're fierce hunters and are not domesticated!
