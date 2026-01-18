#!/usr/bin/env python3
"""
Map Fetcher Module
Fetches and caches monochrome maps from Stadia Maps API (Stamen Toner style)
Supports random city selection from cities.yaml
"""

import os
import random
import logging
from datetime import datetime, timedelta
from pathlib import Path
from typing import Optional, Dict

import requests
import yaml
from PIL import Image

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class MapFetcher:
    """Fetches and caches maps from Stadia Maps API"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize MapFetcher with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.api_key = self.config['stadia_maps']['api_key']
        self.style = self.config['stadia_maps']['style']
        self.map_config = self.config['map']
        self.cache_dir = Path(self.config['cache']['maps_dir'])
        self.cache_dir.mkdir(parents=True, exist_ok=True)

        # Stadia Maps Static API endpoint
        self.base_url = "https://tiles.stadiamaps.com/static/stamen_toner.png"

        # Load cities if random_city is enabled
        self.cities = []
        if self.map_config.get('random_city', False):
            self._load_cities()

    def _load_cities(self):
        """Load cities from cities.yaml"""
        cities_file = self.map_config.get('cities_file', 'cities.yaml')
        try:
            with open(cities_file, 'r') as f:
                cities_data = yaml.safe_load(f)
                self.cities = cities_data.get('cities', [])
                logger.info(f"Loaded {len(self.cities)} cities from {cities_file}")
        except Exception as e:
            logger.error(f"Failed to load cities from {cities_file}: {e}")
            self.cities = []

    def _get_random_city(self) -> Dict:
        """Get random city from cities list"""
        if not self.cities:
            logger.warning("No cities loaded, using default coordinates")
            return {
                'name': 'Default',
                'lat': self.map_config['center_lat'],
                'lon': self.map_config['center_lon'],
                'zoom': self.map_config['zoom']
            }
        city = random.choice(self.cities)
        logger.info(f"Selected random city: {city['name']}")
        return city

    def _get_cache_path(self) -> Path:
        """Get the path for the cached map file"""
        return self.cache_dir / "current_map.png"

    def _is_cache_valid(self) -> bool:
        """Check if cached map exists and is still valid"""
        cache_path = self._get_cache_path()

        if not cache_path.exists():
            logger.info("No cached map found")
            return False

        # Check age of cached file
        file_time = datetime.fromtimestamp(cache_path.stat().st_mtime)
        age = datetime.now() - file_time
        max_age = timedelta(hours=self.map_config['refresh_interval_hours'])

        if age > max_age:
            logger.info(f"Cached map is {age.total_seconds()/3600:.1f} hours old, needs refresh")
            return False

        logger.info(f"Using cached map ({age.total_seconds()/3600:.1f} hours old)")
        return True

    def _fetch_map_from_api(self) -> Optional[Image.Image]:
        """Fetch map from Stadia Maps API"""
        try:
            # Get city coordinates (random or from config)
            if self.map_config.get('random_city', False):
                city = self._get_random_city()
                lat = city['lat']
                lon = city['lon']
                zoom = city.get('zoom', self.map_config['zoom'])
            else:
                lat = self.map_config['center_lat']
                lon = self.map_config['center_lon']
                zoom = self.map_config['zoom']

            width = self.map_config['width']
            height = self.map_config['height']

            # Stadia Maps Static Maps API uses query parameters
            # center is lat,lon (NOT lon,lat!)
            params = {
                'center': f"{lat},{lon}",
                'zoom': zoom,
                'size': f"{width}x{height}@2x",
                'api_key': self.api_key
            }

            logger.info(f"Fetching map from Stadia Maps API...")
            logger.debug(f"URL: {self.base_url} with params: {params}")

            response = requests.get(self.base_url, params=params, timeout=30)
            response.raise_for_status()

            # Load image from response
            from io import BytesIO
            image = Image.open(BytesIO(response.content))
            logger.info(f"Successfully fetched map ({image.size})")

            return image

        except requests.exceptions.RequestException as e:
            logger.error(f"Failed to fetch map from API: {e}")
            return None
        except Exception as e:
            logger.error(f"Error processing map response: {e}")
            return None

    def _crop_attribution_strip(self, image: Image.Image) -> Image.Image:
        """Crop a small strip to remove attribution text."""
        strip_height = max(10, int(image.height * 0.03))
        if image.height <= strip_height:
            logger.warning("Image too small to crop attribution strip")
            return image

        crop_box = (0, 0, image.width, image.height - strip_height)
        cropped = image.crop(crop_box)
        logger.info(f"Cropped attribution strip ({strip_height}px) from bottom")
        return cropped

    def _process_map_for_eink(self, image: Image.Image) -> Image.Image:
        """Convert map to monochrome for e-ink display"""
        # Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')

        # Apply threshold to make it pure black and white
        # Stamen Toner is already high contrast, so gentle threshold
        threshold = 200
        image = image.point(lambda x: 255 if x > threshold else 0, mode='1')

        # Convert back to grayscale for consistency
        image = image.convert('L')

        logger.info("Processed map for e-ink display")
        return image

    def fetch_map(self, force_refresh: bool = False) -> Optional[Image.Image]:
        """
        Fetch map, using cache if valid

        Args:
            force_refresh: Force fetch from API even if cache is valid

        Returns:
            PIL Image object or None if fetch failed
        """
        cache_path = self._get_cache_path()

        # Check cache first
        if not force_refresh and self._is_cache_valid():
            try:
                return Image.open(cache_path)
            except Exception as e:
                logger.error(f"Failed to load cached map: {e}")

        # Fetch from API
        image = self._fetch_map_from_api()

        if image is None:
            # API fetch failed, try to use old cached version as fallback
            if cache_path.exists():
                logger.warning("Using old cached map as fallback")
                try:
                    return Image.open(cache_path)
                except Exception as e:
                    logger.error(f"Failed to load fallback cached map: {e}")
            return None

        # Remove attribution strip from high-res image
        image = self._crop_attribution_strip(image)

        # Downscale before processing for e-ink
        target_size = (self.map_config['width'], self.map_config['height'])
        if image.size != target_size:
            image = image.resize(target_size, Image.Resampling.LANCZOS)

        # Process for e-ink
        image = self._process_map_for_eink(image)

        # Save to cache
        try:
            image.save(cache_path, 'PNG')
            logger.info(f"Saved map to cache: {cache_path}")
        except Exception as e:
            logger.error(f"Failed to save map to cache: {e}")

        return image


def main():
    """Test map fetcher"""
    fetcher = MapFetcher()

    print("Fetching map...")
    map_image = fetcher.fetch_map(force_refresh=True)

    if map_image:
        print(f"Success! Map size: {map_image.size}")
        # Save test output
        test_path = "test_map.png"
        map_image.save(test_path)
        print(f"Saved test map to: {test_path}")
    else:
        print("Failed to fetch map")


if __name__ == "__main__":
    main()
