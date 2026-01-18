# Power Management & Safe Operation Guide

This guide ensures your e-ink display survives power cycles and runs reliably.

## Safe Power Cycling

### ⚡ How to Safely Power Off

**BEST - Proper shutdown:**
```bash
sudo shutdown -h now
# Wait for activity LED to stop blinking (30-60 seconds)
# Then unplug power
```

**ACCEPTABLE - Quick shutdown:**
```bash
sudo poweroff
# Wait for activity LED to stop
# Then unplug
```

**EMERGENCY - If you must unplug immediately:**
The Raspberry Pi can usually handle sudden power loss, but:
- ⚠️ Risk of SD card corruption (small but exists)
- ⚠️ May lose uncommitted cache writes
- ✅ This project is designed to recover gracefully

### 🔌 Powering Back On

Simply plug in the power cable. The system will:

1. **Boot** (30-60 seconds)
2. **Auto-run** the display service
3. **Fetch new city map** (or use cache if <1 hour old)
4. **Fetch new manul** (or use cache)
5. **Update display** (5-10 seconds)

**No manual intervention needed!**

### Recovery from Power Loss

The system is designed to be resilient:

**Cached Data:**
- Maps cached for 1 hour (won't re-fetch if recent)
- Manuls cached for 1 week
- Falls back to old cache if API fails

**Error Handling:**
- Network down? Uses cached map
- Internet down? Uses local manuls
- E-ink error? Logs it and tries again next hour

**Safe Defaults:**
- Read-only operations during display (no file writes during refresh)
- Caches written immediately after download
- No database or state files that could corrupt

## Hourly Auto-Update Setup

### Installation

Run the installation script on your Pi:

```bash
cd ~/e-ink
./install-service.sh
```

This creates:
1. **Boot service**: Runs display on startup
2. **Hourly timer**: Updates every hour
3. **Safe shutdown**: Properly cleans up on poweroff

### What Gets Installed

**Service: `manul-display.service`**
- Runs on boot
- Waits for network
- Auto-restarts on failure

**Timer: `manul-hourly.timer`**
- Triggers every hour
- Randomized 0-5 minute delay (prevents API rate limiting)
- Catches up missed runs if Pi was off

**Safety Features:**
- 10-second graceful shutdown timeout
- Proper cleanup of e-ink display
- Network wait before starting
- Restart on crash

### Managing the Service

```bash
# Check if it's running
sudo systemctl status manul-display.service

# View live logs
journalctl -u manul-display.service -f

# Manual update now
sudo systemctl start manul-display.service

# Check timer schedule
systemctl list-timers manul-hourly.timer

# Stop hourly updates
sudo systemctl stop manul-hourly.timer

# Disable auto-start on boot
sudo systemctl disable manul-display.service

# Re-enable
sudo systemctl enable manul-display.service
sudo systemctl enable manul-hourly.timer
```

## Hourly Refresh Details

### API Usage

**With hourly refreshes:**
- 24 map requests per day
- ~720 map requests per month
- **Well within** free tier (20,000/month)

**New random city every hour!**

### Cache Behavior

The system intelligently caches:

```
Hour 0:  Fetch NYC map → cache for 1 hour
Hour 1:  Cache expired → Fetch Tokyo map
Hour 2:  Cache expired → Fetch Sydney map
...
```

If API fails, uses last successful map.

### Network Requirements

**Internet needed for:**
- Fetching new maps (Stadia Maps API)
- Scraping new manuls (manulization.com)

**Works offline:**
- Uses cached maps (up to 1 hour old)
- Uses local manul photos (if configured)

## SD Card Protection

### Reducing Writes (Optional)

To extend SD card life with hourly writes:

**1. Use RAM for logs (optional):**
```bash
# Edit config.yaml to log to /tmp (RAM)
logging:
  file: "/tmp/manul_display.log"
```

**2. Use tmpfs for cache (advanced):**
```bash
# Add to /etc/fstab
tmpfs /home/pi/e-ink/cache tmpfs defaults,size=100M 0 0
```

**Note:** Not really necessary - modern SD cards handle this fine.

### SD Card Corruption Prevention

**Best practices:**
1. Use quality SD card (SanDisk, Samsung)
2. Proper shutdown when possible
3. Don't unplug during active writes (LED blinking rapidly)
4. Keep Pi in well-ventilated area

**If corruption happens:**
```bash
# On Pi, check filesystem
sudo fsck -f /dev/mmcblk0p2

# Or from another computer with SD card reader
# Linux: sudo fsck -f /dev/sdX2
# macOS: Use Disk Utility First Aid
```

## Monitoring & Debugging

### Check Last Update

```bash
# View last 20 log entries
journalctl -u manul-display.service -n 20

# View errors only
journalctl -u manul-display.service -p err

# Follow live logs
journalctl -u manul-display.service -f
```

### Verify Hourly Timer

```bash
# Check timer is active
systemctl status manul-hourly.timer

# See next scheduled run
systemctl list-timers manul-hourly.timer

# Output example:
# NEXT                         LEFT    LAST                         PASSED
# Sat 2024-01-20 15:00:00 UTC  45min   Sat 2024-01-20 14:00:00 UTC  15min ago
```

### Check Cache Status

```bash
# View cached maps
ls -lh ~/e-ink/cache/maps/

# View cached manuls
ls -lh ~/e-ink/cache/manuls/

# Check cache age
stat ~/e-ink/cache/maps/current_map.png
```

## Troubleshooting

### Display doesn't update after power cycle

**Check service status:**
```bash
sudo systemctl status manul-display.service
```

**If failed, view error:**
```bash
journalctl -u manul-display.service -n 50
```

**Common issues:**
- Network not ready: Service auto-retries
- E-ink not connected: Check GPIO connection
- Permission error: Run `sudo usermod -a -G spi,gpio,i2c pi` and reboot

### Hourly updates not working

**Verify timer is enabled:**
```bash
sudo systemctl status manul-hourly.timer
```

**If inactive:**
```bash
sudo systemctl enable manul-hourly.timer
sudo systemctl start manul-hourly.timer
```

**Check timer logs:**
```bash
journalctl -u manul-hourly.service -n 50
```

### Too many API requests

**Check request count:**
- Login to https://stadiamaps.com/dashboard
- View "Usage"

**If approaching limit:**
1. Increase refresh interval:
```yaml
# config.yaml
map:
  refresh_interval_hours: 2  # Every 2 hours instead
```

2. Adjust timer:
```bash
# Edit timer file
sudo nano /etc/systemd/system/manul-hourly.timer

# Change to every 2 hours:
OnCalendar=0/2:00:00

# Reload
sudo systemctl daemon-reload
sudo systemctl restart manul-hourly.timer
```

### Display shows old city/manul after reboot

**Normal behavior if:**
- Cache is still valid (<1 hour for map)
- Network isn't ready yet

**Force refresh:**
```bash
python3 manul_display.py --refresh-map --rotate-manul
```

## Power Consumption

**Typical power usage:**
- **Idle (between refreshes):** ~2.5W (Pi 4), ~0.5W (Pi Zero 2 W)
- **During refresh:** ~3.5W (Pi 4), ~1W (Pi Zero 2 W)
- **E-ink display:** Negligible (only during refresh)

**Daily consumption:**
- ~24 refreshes/day × 10 seconds = 4 minutes active
- ~23h 56m idle
- **Total: ~60-70 Wh/day** (Pi 4) or **~12-15 Wh/day** (Pi Zero 2 W)

**Annual cost:** ~$3-8 depending on electricity rates and Pi model

## Emergency Procedures

### System won't boot after power loss

1. **Try safe mode:**
   - Remove SD card
   - Insert into computer
   - Check `cmdline.txt` file isn't corrupted
   - Backup files
   - Re-flash if needed

2. **Recover project:**
   - Your project is in `/home/pi/e-ink/`
   - Copy to computer before re-flashing
   - Or re-clone from backup

### E-ink display stuck/ghosted

```bash
# Clear display
python3 -c "from waveshare_epd import epd7in5_V2; epd = epd7in5_V2.EPD(); epd.init(); epd.Clear(); epd.sleep()"

# Force new image
python3 manul_display.py --refresh-map
```

### Disable auto-run temporarily

```bash
# Stop and disable services
sudo systemctl stop manul-hourly.timer
sudo systemctl disable manul-display.service

# Reboot without auto-update
sudo reboot
```

## Best Practices Summary

✅ **DO:**
- Use quality SD card
- Shutdown properly when convenient
- Monitor logs occasionally
- Keep system updated
- Use UPS/battery backup if power is unreliable

✅ **DON'T:**
- Unplug while LED is blinking rapidly
- Run on unreliable power source long-term
- Ignore errors in logs
- Fill up SD card (keep 1GB+ free)

✅ **SAFE TO:**
- Power cycle anytime (designed for it)
- Unplug if needed (emergency okay)
- Leave running 24/7
- Run for months without intervention

---

**TL;DR**: Your Pi is safe to unplug anytime. It will auto-recover and update hourly with new random cities. Just try to do proper shutdowns when convenient for SD card longevity.
