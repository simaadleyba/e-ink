#!/usr/bin/env python3
"""
Manul E-Ink Display - Main Script
Orchestrates map fetching, manul scraping, image processing, and e-ink display
"""

import sys
import logging
import argparse
from pathlib import Path
from typing import Optional

import yaml
from PIL import Image, ImageDraw

# Import our modules
from map_fetcher import MapFetcher
from manul_scraper import ManulScraper
from manul_processor import ManulProcessor

# Set up logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)
logger = logging.getLogger(__name__)


class ManulDisplay:
    """Main display orchestrator"""

    def __init__(self, config_path: str = "config.yaml", test_mode: bool = False):
        """
        Initialize ManulDisplay

        Args:
            config_path: Path to configuration file
            test_mode: If True, save to file instead of displaying on e-ink
        """
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.test_mode = test_mode
        self.display_config = self.config['display']
        self.sidebar_config = self.config['sidebar']

        # Initialize modules
        self.map_fetcher = MapFetcher(config_path)
        self.manul_scraper = ManulScraper(config_path)
        self.manul_processor = ManulProcessor(config_path)

        # E-ink display (only initialize if not in test mode)
        self.epd = None
        if not test_mode:
            try:
                self._init_display()
            except Exception as e:
                logger.error(f"Failed to initialize e-ink display: {e}")
                logger.info("Falling back to test mode")
                self.test_mode = True

    def _init_display(self):
        """Initialize e-ink display"""
        try:
            # Import the appropriate Waveshare library
            # Dynamically import based on model in config
            model = self.display_config['model']

            if model == "epd7in5_V2":
                from waveshare_epd import epd7in5_V2
                self.epd = epd7in5_V2.EPD()
            elif model == "epd7in5":
                from waveshare_epd import epd7in5
                self.epd = epd7in5.EPD()
            else:
                raise ValueError(f"Unsupported display model: {model}")

            logger.info(f"Initializing {model} display...")
            self.epd.init()
            logger.info("Display initialized successfully")

        except ImportError as e:
            logger.error(f"Failed to import waveshare_epd: {e}")
            logger.info("Make sure waveshare-epd library is installed")
            raise
        except Exception as e:
            logger.error(f"Failed to initialize display: {e}")
            raise

    def _compose_layout(self, map_image: Image.Image, sidebar_image: Image.Image) -> Image.Image:
        """
        Compose final layout with map and sidebar

        Args:
            map_image: Processed map image
            sidebar_image: Processed sidebar image with manul and metadata

        Returns:
            Complete composed image ready for display
        """
        width = self.display_config['width']
        height = self.display_config['height']

        # Create blank canvas
        canvas = Image.new('L', (width, height), color=255)  # White background

        # Paste map on left (70%)
        map_x = 0
        map_y = 0
        canvas.paste(map_image, (map_x, map_y))

        # Draw divider line
        draw = ImageDraw.Draw(canvas)
        divider_x = map_image.width
        draw.line([(divider_x, 0), (divider_x, height)], fill=0, width=2)

        # Paste sidebar on right (30%)
        sidebar_x = divider_x + 2
        sidebar_y = (height - sidebar_image.height) // 2  # Center vertically

        # Ensure sidebar doesn't overflow
        if sidebar_image.height > height:
            sidebar_image = sidebar_image.crop((0, 0, sidebar_image.width, height))
            sidebar_y = 0

        canvas.paste(sidebar_image, (sidebar_x, sidebar_y))

        logger.info(f"Composed layout: {canvas.size}")
        return canvas

    def _display_on_eink(self, image: Image.Image):
        """Push image to e-ink display"""
        if self.epd is None:
            raise RuntimeError("E-ink display not initialized")

        try:
            logger.info("Displaying on e-ink screen...")

            # Convert to 1-bit for display
            # Note: Some displays need specific format conversion
            display_image = image.convert('1')

            # Get buffer from image
            buffer = self.epd.getbuffer(display_image)

            # Display the image
            self.epd.display(buffer)

            logger.info("Display updated successfully")

        except Exception as e:
            logger.error(f"Failed to update display: {e}")
            raise

    def refresh_display(self, force_map_refresh: bool = False):
        """
        Complete refresh cycle: fetch map, fetch manul, compose, display

        Args:
            force_map_refresh: Force refresh map from API even if cached
        """
        logger.info("Starting display refresh cycle...")

        # Step 1: Fetch map
        logger.info("Fetching map...")
        map_image = self.map_fetcher.fetch_map(force_refresh=force_map_refresh)

        if map_image is None:
            logger.error("Failed to fetch map, aborting refresh")
            return False

        # Step 2: Fetch manul
        logger.info("Fetching manul...")
        manul_data = self.manul_scraper.get_random_manul()

        if manul_data is None or manul_data.image is None:
            logger.error("Failed to fetch manul, aborting refresh")
            return False

        # Step 3: Process manul image
        logger.info("Processing manul image...")
        sidebar_image = self.manul_processor.einkify_manul(
            manul_data.image,
            manul_data.name,
            manul_data.location,
            manul_data.description
        )

        # Step 4: Compose layout
        logger.info("Composing layout...")
        final_image = self._compose_layout(map_image, sidebar_image)

        # Step 5: Display
        if self.test_mode:
            # Save to file in test mode
            output_path = "test_output.png"
            final_image.save(output_path)
            logger.info(f"Test mode: Saved output to {output_path}")
        else:
            # Display on e-ink
            self._display_on_eink(final_image)

        logger.info("Display refresh complete!")
        return True

    def rotate_manul(self):
        """Rotate to a new manul (keep same map)"""
        logger.info("Rotating manul...")

        # Fetch new manul
        manul_data = self.manul_scraper.get_random_manul()

        if manul_data is None or manul_data.image is None:
            logger.error("Failed to fetch new manul")
            return False

        # Process manul
        sidebar_image = self.manul_processor.einkify_manul(
            manul_data.image,
            manul_data.name,
            manul_data.location,
            manul_data.description
        )

        # Get cached map
        map_image = self.map_fetcher.fetch_map(force_refresh=False)

        if map_image is None:
            logger.error("No cached map available")
            return False

        # Compose and display
        final_image = self._compose_layout(map_image, sidebar_image)

        if self.test_mode:
            output_path = "test_output.png"
            final_image.save(output_path)
            logger.info(f"Test mode: Saved output to {output_path}")
        else:
            self._display_on_eink(final_image)

        logger.info("Manul rotation complete!")
        return True

    def cleanup(self):
        """Clean up resources"""
        if self.epd is not None:
            try:
                logger.info("Putting display to sleep...")
                self.epd.sleep()
            except Exception as e:
                logger.error(f"Error during cleanup: {e}")


def main():
    """Main entry point"""
    parser = argparse.ArgumentParser(description="Manul E-Ink Display")
    parser.add_argument('--test-mode', action='store_true',
                        help='Test mode: save to file instead of displaying')
    parser.add_argument('--refresh-map', action='store_true',
                        help='Force refresh map from API')
    parser.add_argument('--rotate-manul', action='store_true',
                        help='Rotate to new manul (keep current map)')
    parser.add_argument('--config', default='config.yaml',
                        help='Path to config file (default: config.yaml)')

    args = parser.parse_args()

    try:
        # Initialize display
        display = ManulDisplay(config_path=args.config, test_mode=args.test_mode)

        # Perform requested action
        if args.rotate_manul:
            success = display.rotate_manul()
        else:
            success = display.refresh_display(force_map_refresh=args.refresh_map)

        # Cleanup
        display.cleanup()

        sys.exit(0 if success else 1)

    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as e:
        logger.error(f"Fatal error: {e}", exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
