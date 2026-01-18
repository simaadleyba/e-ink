# City Maps Configuration Guide

The map panel can display any of 50+ major cities from Asia, North America, and Oceania.

## How It Works

### Random City Mode (Default)

By default, the system picks a **random city** from `cities.yaml` each time the map refreshes:

```yaml
# In config.yaml
map:
  random_city: true  # Enable random city selection
```

Each map refresh (default: every 24 hours) will show a different city.

### Fixed City Mode

To always show the same city, disable random mode and set specific coordinates:

```yaml
# In config.yaml
map:
  random_city: false
  center_lat: 35.6762   # Tokyo
  center_lon: 139.6503
  zoom: 12
```

## Available Cities (50+)

### 🇺🇸 United States
- **East Coast**: New York City, Boston, Washington DC, Miami
- **West Coast**: San Francisco, Los Angeles, Seattle, Portland, San Diego
- **Other**: Chicago, Austin, Denver

### 🇨🇦 Canada
- Vancouver, Toronto, Montreal

### 🇦🇺 Australia
- Sydney, Melbourne, Brisbane, Perth

### 🇳🇿 New Zealand
- Auckland, Wellington

### 🇯🇵 Japan
- Tokyo, Osaka, Kyoto, Sapporo, Yokohama

### 🇰🇷 South Korea
- Seoul, Busan

### 🇹🇼 Taiwan
- Taipei, Kaohsiung

### 🇻🇳 Vietnam
- Hanoi, Ho Chi Minh City

### 🇹🇭 Thailand
- Bangkok

### 🇸🇬 Singapore
### 🇭🇰 Hong Kong

### 🇨🇳 China
- Shanghai, Beijing, Shenzhen

### 🇵🇭 Philippines
- Manila

### 🇲🇾 Malaysia
- Kuala Lumpur

### 🇮🇩 Indonesia
- Jakarta

### 🇮🇳 India
- Mumbai, Delhi

See `cities.yaml` for the complete list with coordinates.

## Customizing Cities

### Add Your Own City

Edit `cities.yaml`:

```yaml
cities:
  - name: "Your City Name"
    lat: 12.3456     # Latitude
    lon: -78.9012    # Longitude
    zoom: 12         # Zoom level (11-14 recommended for cities)
```

**Finding coordinates**:
1. Go to https://www.google.com/maps
2. Right-click on your city
3. Click the coordinates (they'll copy to clipboard)
4. Format: First number = latitude, Second = longitude

### Remove Cities

Simply delete unwanted entries from `cities.yaml`.

### Filter by Region

Comment out cities you don't want:

```yaml
cities:
  # United States cities
  - name: "New York City, USA"
    lat: 40.7128
    lon: -74.0060
    zoom: 12

  # - name: "Los Angeles, USA"  # Commented out
  #   lat: 34.0522
  #   lon: -118.2437
  #   zoom: 11
```

## Map Style

The display uses **Stamen Toner** style - a high-contrast black & white map perfect for e-ink:

- Black streets and labels
- White background
- Minimal colors (already optimized for e-ink)
- Clear, readable typography

This style was chosen specifically because it looks great on e-ink displays without much processing.

## Zoom Levels

Zoom levels determine how much of the city is visible:

- **Zoom 11**: Wide view (whole metro area)
- **Zoom 12**: City view (recommended default)
- **Zoom 13**: Neighborhood view (more detail)
- **Zoom 14**: Street view (maximum detail)

Example comparison:
```yaml
# Wide metro area view
- name: "Tokyo, Japan"
  lat: 35.6762
  lon: 139.6503
  zoom: 11  # Shows entire Tokyo metro

# Detailed city center
- name: "Tokyo City Center, Japan"
  lat: 35.6762
  lon: 139.6503
  zoom: 14  # Shows specific neighborhoods
```

## Tips

### Create City Collections

You can create multiple cities.yaml files:

```bash
# cities-asia.yaml - Only Asian cities
# cities-usa.yaml - Only US cities
# cities-favorites.yaml - Your favorites
```

Then switch in config.yaml:
```yaml
map:
  cities_file: "cities-asia.yaml"
```

### Test Cities First

Before adding to rotation, test individual cities:

```bash
# Edit config.yaml temporarily
nano config.yaml
# Set random_city: false and add your coordinates

# Test in test mode
python3 manul_display.py --test-mode --refresh-map

# Check test_output.png
```

### Manual City Change

To force a new random city without waiting 24 hours:

```bash
python3 manul_display.py --refresh-map
```

## Troubleshooting

### "No cities loaded, using default coordinates"

**Problem**: cities.yaml not found or has errors

**Solution**:
```bash
# Check file exists
ls cities.yaml

# Check YAML syntax
python3 -c "import yaml; print(yaml.safe_load(open('cities.yaml')))"
```

### Same city appears multiple times

**Normal** - with random selection, cities can repeat. To guarantee rotation:
- Manually change coordinates in config.yaml
- Or implement a "last city" tracker (advanced)

### Map looks wrong for the city

**Issue**: Coordinates might be slightly off

**Solution**:
1. Verify coordinates on Google Maps
2. Adjust zoom level (try 11-14)
3. Fine-tune lat/lon by 0.01-0.05 degrees

### API quota exceeded

**Issue**: Too many map refreshes

**Solution**:
```yaml
# Increase refresh interval
map:
  refresh_interval_hours: 48  # Refresh every 2 days instead
```

Free Stadia Maps tier: 20,000 requests/month
- Daily refreshes: ~30/month (well within limit)
- Hourly refreshes: ~720/month (still safe)

## Examples

### Show Only Japanese Cities

Create `cities-japan.yaml`:
```yaml
cities:
  - name: "Tokyo, Japan"
    lat: 35.6762
    lon: 139.6503
    zoom: 12

  - name: "Osaka, Japan"
    lat: 34.6937
    lon: 135.5023
    zoom: 12

  - name: "Kyoto, Japan"
    lat: 35.0116
    lon: 135.7681
    zoom: 13  # Zoom in closer for Kyoto
```

Update config.yaml:
```yaml
map:
  random_city: true
  cities_file: "cities-japan.yaml"
```

### Always Show New York

```yaml
map:
  random_city: false
  center_lat: 40.7128
  center_lon: -74.0060
  zoom: 12
```

### Rotate Between 3 Favorite Cities

Create `cities-favorites.yaml`:
```yaml
cities:
  - name: "Tokyo, Japan"
    lat: 35.6762
    lon: 139.6503
    zoom: 12

  - name: "San Francisco, USA"
    lat: 37.7749
    lon: -122.4194
    zoom: 12

  - name: "Sydney, Australia"
    lat: -33.8688
    lon: 151.2093
    zoom: 12
```

Update config:
```yaml
map:
  random_city: true
  cities_file: "cities-favorites.yaml"
```

Now your display will randomly rotate between these three cities!

---

**Pro Tip**: The random city feature pairs perfectly with the random manul feature - every refresh gives you a completely new display!
