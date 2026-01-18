# Quick Start Guide

## First Time Setup

1. **Install dependencies:**
   ```bash
   pip3 install -r requirements.txt
   ```

2. **Get API key:**
   - Visit https://stadiamaps.com/
   - Sign up (free)
   - Create API key
   - Copy to `config.yaml`

3. **Test without hardware:**
   ```bash
   python3 manul_display.py --test-mode
   ```

   Check `test_output.png` - you should see a map + manul!

## Daily Usage

### On Raspberry Pi with e-ink display:

```bash
# Full refresh (new map + new manul)
python3 manul_display.py

# Just rotate manul (keep map)
python3 manul_display.py --rotate-manul

# Force new map
python3 manul_display.py --refresh-map
```

### Testing (no hardware needed):

```bash
# Test complete system
python3 manul_display.py --test-mode

# Test map only
python3 map_fetcher.py

# Test manul scraping only
python3 manul_scraper.py

# Test image processing only
python3 manul_processor.py
```

## Configuration Quick Tweaks

Edit `config.yaml`:

### Make images more contrasty:
```yaml
image_processing:
  contrast_boost: 2.5  # Try 2.0-3.0
```

### City maps (50+ cities included!):
```yaml
map:
  random_city: true  # Rotate through random cities
  # OR set specific city:
  random_city: false
  center_lat: 35.6762   # Tokyo
  center_lon: 139.6503
  zoom: 12
```
**See `CITY_MAPS.md` for all 50+ included cities and how to customize!**

### Change refresh timing:
```yaml
map:
  refresh_interval_hours: 48  # Refresh every 2 days

sidebar:
  manul_rotation_hours: 12    # New manul every 12 hours
```

## Troubleshooting Quick Fixes

### Images too dark/light on e-ink:
1. Edit `config.yaml`
2. Change `contrast_boost: 2.5` (try different values)
3. Test with `--test-mode` first

### Can't fetch manuls:
1. Add local manuls to `local_manuls/` folder
2. Update `local_manuls/metadata.json`
3. System will auto-fallback to local

### Display not initializing:
1. Check display is connected properly
2. Enable SPI: `sudo raspi-config` → Interface → SPI → Enable
3. Verify model in config.yaml matches your display

## Auto-Run on Boot (Optional)

Quick cron setup for automatic updates:

```bash
crontab -e
```

Add:
```cron
# Rotate manul every 6 hours
0 */6 * * * cd /home/pi/Desktop/personal/e-ink && python3 manul_display.py --rotate-manul

# Refresh map daily at 6 AM
0 6 * * * cd /home/pi/Desktop/personal/e-ink && python3 manul_display.py --refresh-map
```

## Project Structure

```
e-ink/
├── manul_display.py      ← Main script (run this)
├── map_fetcher.py        ← Gets maps from Stadia
├── manul_scraper.py      ← Scrapes manulization.com
├── manul_processor.py    ← Makes images e-ink ready
├── config.yaml           ← YOUR SETTINGS HERE
├── requirements.txt      ← Dependencies
└── cache/                ← Auto-created, stores cached data
```

## Need Help?

- Full docs: See `README.md`
- Test mode: Always use `--test-mode` when developing
- Logs: Check `manul_display.log` for errors
- Debug: Set `logging.level: "DEBUG"` in config.yaml
