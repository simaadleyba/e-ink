# Complete Raspberry Pi E-Ink Display Setup Guide

This guide walks you through everything from preparing the SD card to running the manul display.

## 📋 What You'll Need

### Hardware
- Raspberry Pi (3, 4, 5, or Zero 2 W)
- Waveshare 7.5" e-ink display (800x480)
- MicroSD card (16GB minimum, 32GB recommended)
- Power supply for Pi
- microSD card reader for your computer
- (Optional) Ethernet cable or WiFi credentials
- (Optional) Monitor + keyboard for initial setup

### Software
- Raspberry Pi Imager (download from https://www.raspberrypi.com/software/)
- Stadia Maps API key (free, from https://stadiamaps.com/)

---

## Step 1: Prepare the SD Card with Raspberry Pi OS

The SD card needs a complete operating system, not just your project files.

### 1.1 Download Raspberry Pi Imager

1. Visit https://www.raspberrypi.com/software/
2. Download for your OS (macOS/Windows/Linux)
3. Install and open the application

### 1.2 Flash Raspberry Pi OS

1. **Insert SD card** into your computer's card reader

2. **Open Raspberry Pi Imager**

3. **Choose Device**:
   - Click "Choose Device"
   - Select your Raspberry Pi model (e.g., Raspberry Pi 4)

4. **Choose OS**:
   - Click "Choose OS"
   - Select **"Raspberry Pi OS (64-bit)"** for desktop interface
   - OR select **"Raspberry Pi OS Lite (64-bit)"** for minimal install (no desktop, less space)
   - Recommended: Regular OS for easier troubleshooting

5. **Choose Storage**:
   - Click "Choose Storage"
   - Select your SD card (⚠️ ALL DATA WILL BE ERASED)

6. **Configure Settings** (IMPORTANT):
   - Click "Next"
   - Click "Edit Settings" when prompted

   **General tab**:
   - Set hostname: `raspberrypi` (or custom name)
   - Set username: `pi` (recommended)
   - Set password: Choose a strong password
   - Configure wireless LAN (if using WiFi):
     - Enter your WiFi SSID (network name)
     - Enter WiFi password
     - Select your country
   - Set locale settings (timezone, keyboard layout)

   **Services tab**:
   - ✅ **Enable SSH** (IMPORTANT - allows remote access)
   - Use password authentication

   - Click "Save"

7. **Write to SD card**:
   - Click "Yes" to apply OS customization settings
   - Click "Yes" to confirm erasing SD card
   - Wait for write + verification (5-15 minutes depending on SD card speed)
   - When complete, click "Continue"

8. **Eject SD card safely** from your computer

---

## Step 2: First Boot & Initial Pi Setup

### 2.1 Hardware Assembly

1. **Insert SD card** into Raspberry Pi's microSD slot
2. **Connect Waveshare e-ink display**:
   - Attach via GPIO header pins (usually a HAT that sits on top)
   - OR connect via ribbon cable if using separate board
   - Refer to Waveshare documentation for your specific model
3. **Connect peripherals** (for first-time setup):
   - Option A: Monitor (HDMI) + USB keyboard + mouse
   - Option B: Use SSH (headless) if you configured WiFi/Ethernet
4. **Connect power last** - Pi will boot automatically

### 2.2 First Boot

- First boot takes **1-3 minutes**
- Pi will resize filesystem and reboot once automatically
- If using monitor: Wait for desktop or login prompt
- If using SSH: Wait 2-3 minutes, then try connecting

### 2.3 Connect to Your Pi

**Option A: Direct Access (Monitor + Keyboard)**
- Login with username/password you set in Imager
- Open Terminal application

**Option B: SSH (Headless - Recommended)**

From your computer's terminal:
```bash
# Replace 'pi' with your username if different
# Replace 'raspberrypi.local' with your hostname if different
ssh pi@raspberrypi.local

# If .local doesn't work, find IP address on your router
# and use: ssh pi@192.168.1.XXX
```

Enter the password you set during SD card preparation.

---

## Step 3: Update System & Install Dependencies

Once logged into your Pi (via SSH or terminal):

### 3.1 Update System

```bash
# Update package list
sudo apt update

# Upgrade installed packages (may take 10-20 minutes)
sudo apt upgrade -y
```

### 3.2 Install Python & System Dependencies

```bash
# Install Python 3 and pip
sudo apt install -y python3-pip python3-pil python3-numpy

# Install additional libraries needed for image processing
sudo apt install -y python3-opencv

# Install git (useful for project transfer)
sudo apt install -y git
```

### 3.3 Enable SPI Interface (REQUIRED for e-ink display)

```bash
# Open Raspberry Pi configuration tool
sudo raspi-config
```

Navigate using arrow keys:
1. Select **"Interface Options"** → Press Enter
2. Select **"SPI"** → Press Enter
3. Select **"Yes"** to enable SPI → Press Enter
4. Select **"Ok"** → Press Enter
5. Select **"Finish"** → Press Enter
6. Reboot when prompted: **"Yes"**

Or use command line to enable SPI:
```bash
sudo raspi-config nonint do_spi 0
sudo reboot
```

Wait for Pi to reboot (about 1 minute), then reconnect.

---

## Step 4: Transfer Project to Raspberry Pi

Choose one of these methods:

### Method A: SCP (Secure Copy - Recommended)

From your **Mac/computer terminal** (NOT on the Pi):

```bash
# Navigate to parent directory containing e-ink folder
cd /Users/simaadleyba/Desktop/personal

# Copy entire folder to Pi's home directory
scp -r e-ink pi@raspberrypi.local:~/

# Enter password when prompted
# Transfer takes 1-2 minutes
```

### Method B: Git (If you use version control)

On your **Mac**:
```bash
cd /Users/simaadleyba/Desktop/personal/e-ink
git init
git add .
git commit -m "Initial E-Ink Manul Display project"
# Push to GitHub/GitLab (create repo first)
git remote add origin <your-repo-url>
git push -u origin main
```

On your **Raspberry Pi**:
```bash
cd ~
git clone <your-repo-url>
cd e-ink
```

### Method C: USB Drive

1. Copy `e-ink` folder to USB drive from your computer
2. Plug USB drive into Raspberry Pi
3. On Pi:
```bash
# Find USB drive (usually /media/pi/USB_NAME)
ls /media/pi/

# Copy to home directory
cp -r /media/pi/USB_NAME/e-ink ~/
cd ~/e-ink
```

---

## Step 5: Install Project Dependencies

On your Raspberry Pi, in the project directory:

```bash
# Navigate to project
cd ~/e-ink

# Install all Python packages from requirements.txt
pip3 install -r requirements.txt

# This will install:
# - Pillow (image processing)
# - numpy (arrays)
# - opencv-python (CLAHE)
# - beautifulsoup4 (web scraping)
# - requests (HTTP)
# - PyYAML (config)
# - waveshare-epd (e-ink driver)
# - lxml (HTML parsing)

# Installation takes 5-10 minutes
```

---

## Step 6: Get Stadia Maps API Key

You need a free API key to fetch maps.

### 6.1 Sign Up for Stadia Maps

1. Go to https://stadiamaps.com/
2. Click **"Sign Up"** (top right)
3. Create free account
4. Verify email

### 6.2 Create API Key

1. Log in to Stadia Maps dashboard
2. Click **"Manage Properties"** or **"API Keys"**
3. Click **"Create API Key"** or **"New Property"**
4. Give it a name: `Manul E-Ink Display`
5. Copy the API key (long string of characters)

**Free tier includes**: 20,000 map requests/month (plenty for this project)

---

## Step 7: Configure Your Project

### 7.1 Edit Configuration File

```bash
# On your Pi, in the e-ink folder
nano config.yaml
```

### 7.2 Add API Key

Find this section (around line 5):
```yaml
stadia_maps:
  api_key: "YOUR_API_KEY_HERE"  # Get from https://stadiamaps.com/
```

Replace `YOUR_API_KEY_HERE` with your actual API key:
```yaml
stadia_maps:
  api_key: "abc123xyz789youractualkey"
```

### 7.3 Adjust Map Settings (Optional)

Scroll down to map settings and customize as desired:
```yaml
map:
  center_lat: 40.7128   # NYC
  center_lon: -74.0060
  zoom: 12              # Higher = more zoomed in
```

### 7.4 Save and Exit

- Press `Ctrl + X`
- Press `Y` to confirm save
- Press `Enter` to confirm filename

---

## Step 8: Test Your Setup

### 8.1 Test Without Display (Safe First Test)

```bash
# Run in test mode (creates test_output.png file)
python3 manul_display.py --test-mode
```

This should:
- Fetch a map from Stadia Maps
- Scrape a random manul from manulization.com
- Process the image
- Create `test_output.png`

**Check the output**:
```bash
# If using desktop, open the image
xdg-open test_output.png

# Or copy to your computer to view
# From your Mac terminal:
scp pi@raspberrypi.local:~/e-ink/test_output.png ~/Desktop/
```

### 8.2 Test Individual Modules

Test each component separately:

```bash
# Test map fetching only
python3 map_fetcher.py
# Creates test_map.png

# Test manul scraping only
python3 manul_scraper.py
# Creates test_manul.png (if successful)

# Test image processing only
python3 manul_processor.py
# Creates test_processed_manul.png
```

### 8.3 Test With Real E-Ink Display

⚠️ **Only do this if test mode worked!**

```bash
# Full refresh (map + manul)
python3 manul_display.py
```

This will:
- Initialize e-ink display
- Fetch and display map + manul
- Take 5-10 seconds for full refresh

---

## Step 9: Usage & Commands

### Daily Usage

```bash
cd ~/e-ink

# Full refresh (new map + new manul)
python3 manul_display.py

# Rotate to new manul (keep same map)
python3 manul_display.py --rotate-manul

# Force refresh map from API (ignore cache)
python3 manul_display.py --refresh-map

# Test mode (save to file, don't use display)
python3 manul_display.py --test-mode
```

---

## Step 10: Automation (RECOMMENDED)

### Easy Installation (Recommended)

We provide an automated installer that sets up:
- ✅ Auto-run on boot
- ✅ Hourly map updates (new random city each hour!)
- ✅ Safe power cycle handling
- ✅ Automatic recovery from errors

Simply run:

```bash
cd ~/e-ink
./install-service.sh
```

That's it! The system is now fully automated. See `POWER_MANAGEMENT.md` for details.

**Skip to Step 11 if you used the installer!**

---

### Manual Installation (Advanced)

If you want to set things up manually:

#### Option A: Auto-Run on Boot (systemd)

Create a service that runs the display on boot:

```bash
# Create service file
sudo nano /etc/systemd/system/manul-display.service
```

Paste this content:
```ini
[Unit]
Description=Manul E-Ink Display
After=network-online.target
Wants=network-online.target

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pi/e-ink/manul_display.py
WorkingDirectory=/home/pi/e-ink
User=pi
StandardOutput=journal
StandardError=journal

[Install]
WantedBy=multi-user.target
```

Save (Ctrl+X, Y, Enter) and enable:

```bash
# Reload systemd
sudo systemctl daemon-reload

# Enable service (starts on boot)
sudo systemctl enable manul-display.service

# Start service now (test)
sudo systemctl start manul-display.service

# Check status
sudo systemctl status manul-display.service

# View logs
journalctl -u manul-display.service -f
```

#### Option B: Hourly Updates with Timer (Recommended if doing manual)

Better than cron - uses systemd timers for hourly updates:

```bash
# Create timer service
sudo nano /etc/systemd/system/manul-hourly.service
```

Add:
```ini
[Unit]
Description=Manul E-Ink Display Hourly Update

[Service]
Type=oneshot
ExecStart=/usr/bin/python3 /home/pi/e-ink/manul_display.py --refresh-map
WorkingDirectory=/home/pi/e-ink
User=pi
```

Create timer:
```bash
sudo nano /etc/systemd/system/manul-hourly.timer
```

Add:
```ini
[Unit]
Description=Manul Hourly Timer

[Timer]
OnCalendar=hourly
Persistent=true

[Install]
WantedBy=timers.target
```

Enable:
```bash
sudo systemctl daemon-reload
sudo systemctl enable manul-hourly.timer
sudo systemctl start manul-hourly.timer
```

---

## 📊 Troubleshooting

### "Failed to initialize e-ink display"

**Check**:
- Display is properly connected to GPIO pins
- SPI is enabled: `ls /dev/spi*` (should show `/dev/spidev0.0`)
- Display model in config.yaml matches your hardware
- Try: `sudo usermod -a -G spi,gpio pi` and reboot

### "Failed to fetch map from API"

**Check**:
- API key is correct in config.yaml (no quotes issues, no spaces)
- Internet connection: `ping google.com`
- API quota: Check dashboard at https://stadiamaps.com/
- Test URL directly: Check logs for the actual URL being called

### "Failed to fetch manul"

**Normal** - web scraping can fail. Solutions:
- Add local manul photos to `local_manuls/` folder
- Edit `local_manuls/metadata.json` with photo info
- System will auto-fallback to local storage

### Images look bad on e-ink

**Adjust contrast**:
```bash
nano config.yaml
# Change line ~32:
#   contrast_boost: 2.5  # Try 2.0-3.0
```

Test with `--test-mode` first to see results before updating display.

### Permission denied errors

```bash
# Add user to necessary groups
sudo usermod -a -G spi,gpio,i2c pi

# Reboot
sudo reboot
```

### Module import errors

```bash
# Reinstall dependencies
pip3 install --upgrade -r requirements.txt

# Or install system-wide
sudo pip3 install -r requirements.txt
```

---

## 🎨 Customization Tips

### Change Map Location

Edit `config.yaml`:
```yaml
map:
  center_lat: 35.6762   # Tokyo
  center_lon: 139.6503
  zoom: 11
```

### Adjust Image Contrast

```yaml
image_processing:
  contrast_boost: 2.5    # Higher = more contrast
  use_clahe: true        # Try CLAHE instead
```

### Change Update Frequency

```yaml
map:
  refresh_interval_hours: 48  # Refresh every 2 days

sidebar:
  manul_rotation_hours: 12    # New manul every 12 hours
```

---

## 📁 Quick Reference

### Project Structure
```
e-ink/
├── manul_display.py      ← Main script (run this)
├── map_fetcher.py        ← Gets maps
├── manul_scraper.py      ← Scrapes manuls
├── manul_processor.py    ← Processes images
├── config.yaml           ← YOUR SETTINGS
├── requirements.txt      ← Dependencies
├── cache/                ← Auto-created caches
└── local_manuls/         ← Optional local photos
```

### Common Commands
```bash
# Test mode
python3 manul_display.py --test-mode

# Full refresh
python3 manul_display.py

# New manul only
python3 manul_display.py --rotate-manul

# New map
python3 manul_display.py --refresh-map

# Check logs
cat manul_display.log

# View recent errors
journalctl -u manul-display.service -n 50
```

---

## ✅ Success Checklist

- [ ] SD card flashed with Raspberry Pi OS
- [ ] Pi boots successfully
- [ ] Can connect via SSH or terminal
- [ ] System updated (`sudo apt update && sudo apt upgrade`)
- [ ] SPI interface enabled
- [ ] Project files transferred to Pi
- [ ] Python dependencies installed
- [ ] Stadia Maps API key added to config.yaml
- [ ] Test mode works (`test_output.png` created successfully)
- [ ] E-ink display shows map + manul
- [ ] (Optional) Auto-start or cron configured

---

## 🆘 Need Help?

1. **Check logs**: `cat manul_display.log` or `journalctl -u manul-display.service`
2. **Test mode**: Always test with `--test-mode` first
3. **Module tests**: Test components individually (map_fetcher.py, etc.)
4. **Verbose logging**: Set `logging.level: "DEBUG"` in config.yaml

## 📚 Additional Resources

- Raspberry Pi Documentation: https://www.raspberrypi.com/documentation/
- Waveshare E-Ink Displays: https://www.waveshare.com/wiki/7.5inch_e-Paper_HAT
- Stadia Maps API Docs: https://docs.stadiamaps.com/
- Full project README: See `README.md`
- Quick reference: See `QUICKSTART.md`

---

**You're all set! Enjoy your manul display! 🐱**
