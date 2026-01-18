#!/usr/bin/env python3
"""
Manul Processor Module
E-inkifies manul photos for optimal display on e-ink screens
Includes contrast enhancement, quantization, dithering, and text rendering
"""

import logging
from typing import Optional
from textwrap import wrap

import yaml
import numpy as np
from PIL import Image, ImageDraw, ImageFont, ImageEnhance
import cv2

# Set up logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


class ManulProcessor:
    """Processes manul images for e-ink display"""

    def __init__(self, config_path: str = "config.yaml"):
        """Initialize ManulProcessor with configuration"""
        with open(config_path, 'r') as f:
            self.config = yaml.safe_load(f)

        self.img_config = self.config['image_processing']
        self.text_config = self.config['text']
        self.sidebar_width = self.config['sidebar']['width']
        self.display_height = self.config['display']['height']

    def _enhance_contrast(self, image: Image.Image) -> Image.Image:
        """Enhance image contrast for e-ink display"""
        if self.img_config['use_clahe']:
            # Use CLAHE (Contrast Limited Adaptive Histogram Equalization)
            logger.info("Applying CLAHE contrast enhancement")

            # Convert to numpy array
            img_array = np.array(image)

            # Apply CLAHE
            clahe = cv2.createCLAHE(
                clipLimit=self.img_config['clahe_clip_limit'],
                tileGridSize=(
                    self.img_config['clahe_tile_grid_size'],
                    self.img_config['clahe_tile_grid_size']
                )
            )
            enhanced = clahe.apply(img_array)

            return Image.fromarray(enhanced)
        else:
            # Use simple contrast enhancement
            logger.info(f"Applying contrast boost: {self.img_config['contrast_boost']}x")
            enhancer = ImageEnhance.Contrast(image)
            return enhancer.enhance(self.img_config['contrast_boost'])

    def _quantize_to_palette(self, image: Image.Image) -> Image.Image:
        """Quantize image to limited color palette with dithering"""
        num_colors = self.img_config['palette_colors']

        if self.img_config['dithering']:
            # Use Floyd-Steinberg dithering
            logger.info(f"Quantizing to {num_colors} colors with dithering")
            # Convert to 'P' mode with dithering
            image = image.convert('P', palette=Image.ADAPTIVE, colors=num_colors, dither=Image.FLOYDSTEINBERG)
        else:
            # No dithering
            logger.info(f"Quantizing to {num_colors} colors without dithering")
            image = image.convert('P', palette=Image.ADAPTIVE, colors=num_colors)

        # Convert back to grayscale
        return image.convert('L')

    def _resize_to_sidebar(self, image: Image.Image, max_height: int = None) -> Image.Image:
        """Resize image to fit sidebar width while maintaining aspect ratio"""
        if max_height is None:
            max_height = self.display_height - 150  # Leave room for text

        # Calculate new size maintaining aspect ratio
        width_ratio = self.sidebar_width / image.width
        new_width = self.sidebar_width
        new_height = int(image.height * width_ratio)

        # Ensure it doesn't exceed max height
        if new_height > max_height:
            height_ratio = max_height / new_height
            new_height = max_height
            new_width = int(new_width * height_ratio)

        logger.info(f"Resizing image from {image.size} to ({new_width}, {new_height})")
        return image.resize((new_width, new_height), Image.Resampling.LANCZOS)

    def _render_metadata(self, name: str, location: str, description: str, image_width: int) -> Image.Image:
        """Render metadata text as image"""
        # Create canvas for text
        text_height = 150  # Approximate height for text
        text_image = Image.new('L', (image_width, text_height), color=255)  # White background
        draw = ImageDraw.Draw(text_image)

        # Try to load a font, fallback to default
        try:
            # Try to use a monospace font for better readability
            font = ImageFont.truetype("/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
                                       self.text_config['font_size'])
        except:
            logger.warning("Could not load custom font, using default")
            font = ImageFont.load_default()

        # Prepare text
        y_position = 5
        line_spacing = self.text_config['line_spacing']

        # Draw name (bold/larger by using it twice with offset for poor-man's bold)
        draw.text((5, y_position), name, fill=0, font=font)
        draw.text((6, y_position), name, fill=0, font=font)  # Slight offset for "bold"
        y_position += self.text_config['font_size'] + line_spacing + 2

        # Draw location
        if location and location != "Unknown":
            location_text = f"Location: {location}"
            # Wrap location text if too long
            char_width = image_width // (self.text_config['font_size'] // 2)
            wrapped_location = wrap(location_text, width=char_width)
            for line in wrapped_location[:2]:  # Max 2 lines
                draw.text((5, y_position), line, fill=0, font=font)
                y_position += self.text_config['font_size'] + line_spacing

        # Draw description
        if description:
            # Wrap description text
            char_width = image_width // (self.text_config['font_size'] // 2)
            wrapped_desc = wrap(description, width=char_width)
            for line in wrapped_desc[:4]:  # Max 4 lines for description
                draw.text((5, y_position), line, fill=0, font=font)
                y_position += self.text_config['font_size'] + line_spacing

        # Crop to actual used height
        if y_position < text_height:
            text_image = text_image.crop((0, 0, image_width, y_position + 5))

        return text_image

    def einkify_manul(self, image: Image.Image, name: str, location: str, description: str) -> Image.Image:
        """
        Complete e-inkification pipeline for manul image

        Args:
            image: PIL Image object
            name: Manul name
            location: Manul location
            description: Manul description

        Returns:
            Processed PIL Image ready for e-ink display (includes metadata)
        """
        logger.info(f"Processing manul image: {name}")

        # Step 1: Convert to grayscale
        if image.mode != 'L':
            image = image.convert('L')
            logger.info("Converted to grayscale")

        # Step 2: Enhance contrast
        image = self._enhance_contrast(image)

        # Step 3: Quantize to limited palette with dithering
        image = self._quantize_to_palette(image)

        # Step 4: Resize to sidebar width
        image = self._resize_to_sidebar(image)

        # Step 5: Render metadata text
        text_image = self._render_metadata(name, location, description, image.width)

        # Step 6: Combine image and text
        total_height = image.height + text_image.height
        combined = Image.new('L', (self.sidebar_width, total_height), color=255)

        # Center the image horizontally if it's narrower than sidebar
        x_offset = (self.sidebar_width - image.width) // 2
        combined.paste(image, (x_offset, 0))
        combined.paste(text_image, (x_offset, image.height))

        logger.info(f"Final sidebar image size: {combined.size}")
        return combined


def main():
    """Test manul processor"""
    processor = ManulProcessor()

    # Create a test image
    print("Creating test image...")
    test_image = Image.new('L', (400, 300), color=128)
    from PIL import ImageDraw
    draw = ImageDraw.Draw(test_image)
    for i in range(0, 400, 20):
        draw.rectangle([i, 0, i+10, 300], fill=200)

    # Process it
    print("Processing image...")
    result = processor.einkify_manul(
        test_image,
        name="Test Manul",
        location="Test Location, Mongolia",
        description="This is a test manul with a description that might be quite long and needs to wrap across multiple lines."
    )

    # Save result
    result.save("test_processed_manul.png")
    print(f"Saved test result to: test_processed_manul.png")
    print(f"Final size: {result.size}")


if __name__ == "__main__":
    main()
