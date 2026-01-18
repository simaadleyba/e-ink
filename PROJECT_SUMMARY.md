# E-Ink Manul Display - Project Summary

## What You Have

A complete Raspberry Pi + Waveshare 7.5" e-ink display system that shows:
- **70% Map Panel**: Random major city from 50+ cities (Asia, North America, Oceania)
- **30% Sidebar**: Random manul (Pallas's cat) photo with metadata
- **Auto-Updates**: New random city every hour
- **Power-Safe**: Survives power cycles, auto-recovers

## Quick Start

### On Your Computer (Mac)

1. **Get Stadia Maps API Key**:
   - https://stadiamaps.com/ → Sign up (free)
   - Create API key
   - Edit `config.yaml` and paste your key

2. **Transfer to SD Card**:
   ```bash
   cd /Users/simaadleyba/Desktop/personal
   scp -r e-ink pi@raspberrypi.local:~/
   ```

### On Raspberry Pi

3. **Install Dependencies**:
   ```bash
   cd ~/e-ink
   pip3 install -r requirements.txt
   ```

4. **Enable SPI**:
   ```bash
   sudo raspi-config
   # Interface Options → SPI → Enable
   ```

5. **Setup Auto-Run (Hourly Updates)**:
   ```bash
   ./install-service.sh
   ```

6. **Done!** Display updates every hour with new random city + manul.

## Files Created

```
e-ink/
├── manul_display.py          # Main script
├── map_fetcher.py            # Stadia Maps client (with city rotation)
├── manul_scraper.py          # Web scraper
├── manul_processor.py        # Image processing
├── config.yaml               # Configuration (hourly refresh enabled)
├── cities.yaml               # 50+ cities list
├── requirements.txt          # Dependencies
├── install-service.sh        # Auto-installer (NEW!)
├── cache/                    # Auto-created
├── local_manuls/             # Local fallback storage
│   ├── metadata.json
│   └── README.txt
├── README.md                 # Full documentation
├── SETUP_GUIDE.md            # Complete setup walkthrough
├── QUICKSTART.md             # Quick reference
├── CITY_MAPS.md              # City configuration guide
├── POWER_MANAGEMENT.md       # Power cycling & safety (NEW!)
└── .gitignore                # Git ignore rules
```

## Key Features

### 1. Random City Maps
- 50+ pre-configured cities
- New random city every hour
- High-contrast Stamen Toner style
- Perfect for e-ink

**Cities include:**
- 🇺🇸 US: NYC, SF, LA, Seattle, Boston, Chicago...
- 🇨🇦 Canada: Vancouver, Toronto, Montreal
- 🇯🇵 Japan: Tokyo, Osaka, Kyoto, Sapporo...
- 🇰🇷 South Korea: Seoul, Busan
- 🇹🇼 Taiwan: Taipei, Kaohsiung
- 🇻🇳 Vietnam: Hanoi, Ho Chi Minh City
- 🇦🇺 Australia: Sydney, Melbourne, Brisbane, Perth
- 🇳🇿 New Zealand: Auckland, Wellington
- + many more in Asia

### 2. Manul Photos
- Scraped from manulization.com
- Or use local photos (fallback)
- E-ink optimized (contrast, dithering)
- Metadata included (name, location, description)

### 3. Hourly Auto-Update
- New city every hour
- Smart caching (saves API calls)
- Runs on boot
- Safe power cycling

### 4. Power-Safe Design
- Survives sudden power loss
- Auto-recovers on boot
- Falls back to cache if offline
- No corruption issues

## Configuration

Everything is configurable in `config.yaml`:

```yaml
# Hourly city rotation (default)
map:
  random_city: true
  refresh_interval_hours: 1

# Or fixed city
map:
  random_city: false
  center_lat: 35.6762  # Tokyo
  center_lon: 139.6503
  zoom: 12
```

## Commands

```bash
# Test mode (no hardware needed)
python3 manul_display.py --test-mode

# Manual refresh
python3 manul_display.py --refresh-map

# View logs
journalctl -u manul-display.service -f

# Check next update
systemctl list-timers manul-hourly.timer
```

## Power Cycling

**Safe to unplug anytime!** System will:
1. Auto-boot
2. Auto-run display service
3. Fetch new city (or use <1hr cache)
4. Update display

No manual intervention needed.

**Best practice**: Proper shutdown when convenient
```bash
sudo shutdown -h now
```

## Customization

### Add Your Own City

Edit `cities.yaml`:
```yaml
cities:
  - name: "Your City"
    lat: 12.3456
    lon: -78.9012
    zoom: 12
```

### Change Update Frequency

Edit `config.yaml`:
```yaml
map:
  refresh_interval_hours: 2  # Every 2 hours
```

Then restart timer:
```bash
sudo systemctl restart manul-hourly.timer
```

### Add Local Manul Photos

1. Add photos to `local_manuls/`
2. Edit `local_manuls/metadata.json`
3. System auto-falls back if scraping fails

## Troubleshooting

### Check Service Status
```bash
sudo systemctl status manul-display.service
sudo systemctl status manul-hourly.timer
```

### View Errors
```bash
journalctl -u manul-display.service -p err
```

### Force Update
```bash
sudo systemctl start manul-display.service
```

### Test Without Hardware
```bash
python3 manul_display.py --test-mode
# Check test_output.png
```

## API Usage

**Free tier: 20,000 requests/month**

**Your usage:**
- 24 hourly updates/day = 720 requests/month
- Well within limit! ✅

## Documentation

- `README.md` - Full documentation
- `SETUP_GUIDE.md` - Step-by-step setup (SD card to working display)
- `QUICKSTART.md` - Quick command reference
- `CITY_MAPS.md` - City configuration details
- `POWER_MANAGEMENT.md` - Power cycling, hourly updates, safety

## Architecture

**Modular design:**
- `map_fetcher.py` - Handles Stadia Maps API + city rotation
- `manul_scraper.py` - Web scraping with fallback
- `manul_processor.py` - E-ink image optimization
- `manul_display.py` - Orchestration + e-ink driver

**All components testable independently!**

## What Makes This Special

✨ **City Rotation**: Unlike static displays, shows 50+ different cities
✨ **Hourly Updates**: Always fresh content
✨ **Power Safe**: No babysitting needed - just plug in and go
✨ **Self-Healing**: Cache fallbacks, retry logic, graceful degradation
✨ **E-Ink Optimized**: Proper contrast, dithering, quantization
✨ **Zero Maintenance**: Set and forget

## Next Steps

After initial setup:

1. **Just let it run!** Updates hourly automatically
2. (Optional) Add your favorite cities to `cities.yaml`
3. (Optional) Add local manul photos for offline use
4. (Optional) Customize contrast in `config.yaml`

## Support

- Check documentation in project folder
- View logs: `journalctl -u manul-display.service -f`
- Test mode: `python3 manul_display.py --test-mode`

---

**Enjoy your ever-changing manul display!** 🗺️ + 🐱 = ✨
