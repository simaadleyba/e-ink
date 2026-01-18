# Raspberry Pi E-Ink Manul Display Project

## Overview
Build a Raspberry Pi + Waveshare 7.5″ e-ink display that shows:
- **Main panel (70%):** Static map (Stamen Maps/Stadia, monochrome)
- **Sidebar (30%):** Rotating e-inkified manul photos with metadata

## Hardware
- Raspberry Pi (any recent model)
- Waveshare 7.5″ e-ink display (black/white)
- SD card (for local manul photos or system storage)

## Core Requirements

### 1. Map Panel
- Fetch Stamen Maps (Toner or Terrain style) from Stadia Maps API
- Render server-side as PNG
- Convert to monochrome (grayscale)
- Resize/crop to fit 70% of display width
- Cache locally to minimize API calls (daily refresh acceptable)

### 2. Sidebar: Manul Photo + Metadata
- **Source:** Scrape random manul from `https://manulization.com/manuls/` OR use local SD card folder
- **Image processing (e-inkification):**
  - Load image (any format)
  - Convert to grayscale
  - Boost contrast using CLAHE or PIL Contrast enhancement (2.0–2.5×)
  - Quantize to 4-color palette (dithering preferred)
  - Resize to sidebar width (match e-ink constraints)
- **Metadata display below image:**
  - Manul name
  - Location/origin
  - Brief description or fun fact (if available)
  - Display as monochrome text

### 3. Display Composition
- Layout: Map (70%) + Sidebar (30%), side-by-side
- Sidebar width: TBD (e-ink layout constraint)
- Refresh cadence:
  - Map: daily or manual
  - Manul: rotate on button press OR auto-rotate every 6–12 hours

### 4. Data Fetching
**Option A (web scraping):**
- Scrape `https://manulization.com/manuls/` for available manul pages
- Parse HTML to extract image URL, name, location, description
- Fetch random manul on each rotation

**Option B (local storage):**
- Store manul photos + metadata (JSON or CSV) on SD card
- Rotate through local folder
- No internet dependency

**Recommendation:** Implement both (scrape on startup, fall back to local if offline)

### 5. E-Ink Driver
- Use Waveshare's official Python library or `waveshare-epd`
- Push final composite image to display
- Handle partial refresh vs full refresh (full refresh ~3–5 sec, slower but cleaner)

## Technical Stack
- **Language:** Python 3
- **Image processing:** PIL/Pillow, NumPy, OpenCV (for CLAHE)
- **Web scraping:** BeautifulSoup4 or Selenium (for JavaScript-heavy sites)
- **E-ink driver:** `waveshare-epd` or Waveshare's official library
- **Maps API:** Stadia Maps (free tier available)
- **Optional:** requests, cron for scheduled refreshes

## Deliverables
1. **Main script** (`manul_display.py`):
   - Fetch/cache map
   - Fetch/load manul photo + metadata
   - E-inkify image (contrast boost + quantize)
   - Compose layout (map + sidebar)
   - Push to e-ink display

2. **Helper modules:**
   - `manul_scraper.py` — fetch random manul from web
   - `manul_processor.py` — image e-inkification (grayscale, CLAHE, quantize)
   - `map_fetcher.py` — fetch Stamen map from Stadia Maps

3. **Config file** (`config.yaml`):
   - API keys (Stadia Maps)
   - Display dimensions
   - Sidebar width (pixels)
   - Refresh intervals
   - Local manul folder path

4. **Requirements file** (`requirements.txt`):
   - All dependencies

## Optional Enhancements
- Button/GPIO input to manually rotate manul
- Cron job for auto-refresh
- Fallback images if scraping fails
- Error logging + graceful degradation
- Power management (Pi sleep mode between refreshes)

## Start With
1. Set up e-ink display library + test basic rendering
2. Fetch one Stamen map, convert to monochrome
3. Scrape or load one manul photo, e-inkify it
4. Compose layout (map + sidebar)
5. Push to display
6. Add rotation logic + cron scheduling

---

**Key constraint:** E-ink = low refresh, low contrast. Keep images high-contrast for clarity. Test contrast boost levels (2.0–2.5×) to find sweet spot.
