#!/usr/bin/env python3
"""E-ink dashboard showing time, reminders, and weather."""

from __future__ import annotations

import argparse
import logging
import sys
from datetime import datetime
from pathlib import Path
from typing import List
from zoneinfo import ZoneInfo

import yaml
from PIL import Image, ImageDraw

from reminders_provider import RemindersProvider, ReminderItem
from render_utils import draw_text_lines, load_font, wrap_text
from weather_provider import WeatherProvider


logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s",
)
logger = logging.getLogger(__name__)


class Dashboard:
    """Main dashboard orchestrator."""

    def __init__(self, config_path: str = "config.yaml", test_mode: bool = False):
        self.config_path = Path(config_path)
        self.config = yaml.safe_load(self.config_path.read_text(encoding="utf-8"))

        self.test_mode = test_mode
        self.display_config = self.config["display"]
        self.dashboard_config = self.config.get("dashboard", {})
        self.text_config = self.config.get("text", {})

        self.timezone = ZoneInfo(self.dashboard_config.get("timezone", "Europe/Istanbul"))

        self.font_path = self.text_config.get(
            "font_path",
            "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf",
        )
        self.font_size = int(self.text_config.get("font_size", 18))
        self.header_font_size = int(self.text_config.get("header_font_size", 28))
        self.line_spacing = int(self.text_config.get("line_spacing", 6))
        self.section_spacing = int(self.text_config.get("section_spacing", 16))

        self.reminders_provider = RemindersProvider(self.config)
        self.weather_provider = WeatherProvider(self.config)

        self.epd = None
        if not test_mode:
            self._init_display()

    def _init_display(self) -> None:
        model = self.display_config.get("model", "epd7in5_V2")
        try:
            if model == "epd7in5_V2":
                from waveshare_epd import epd7in5_V2

                self.epd = epd7in5_V2.EPD()
            elif model == "epd7in5":
                from waveshare_epd import epd7in5

                self.epd = epd7in5.EPD()
            else:
                raise ValueError(f"Unsupported display model: {model}")

            logger.info("Initializing %s display...", model)
            self.epd.init()
            logger.info("Display initialized successfully")
        except ImportError as exc:
            logger.error("Failed to import waveshare_epd: %s", exc)
            logger.info("Make sure waveshare-epd library is installed")
            raise

    def _render_header(self, draw: ImageDraw.ImageDraw, width: int, y: int) -> int:
        header_font = load_font(self.font_path, self.header_font_size)
        now = datetime.now(self.timezone)
        date_str = now.strftime("%A, %d %B %Y")
        time_str = now.strftime("%H:%M")

        draw.text((24, y), date_str, font=header_font, fill=0)
        time_width = header_font.getlength(time_str)
        draw.text((width - time_width - 24, y), time_str, font=header_font, fill=0)

        return y + header_font.size + self.section_spacing

    def _render_reminders(
        self,
        draw: ImageDraw.ImageDraw,
        reminders: List[ReminderItem],
        x: int,
        y: int,
        max_width: int,
        max_height: int,
    ) -> int:
        title_font = load_font(self.font_path, self.header_font_size - 6)
        body_font = load_font(self.font_path, self.font_size)

        draw.text((x, y), "Reminders", font=title_font, fill=0)
        y += title_font.size + self.line_spacing

        if not reminders:
            draw.text((x, y), "No reminders", font=body_font, fill=0)
            return y + body_font.size

        for item in reminders:
            prefix = "• "
            available_width = max_width - body_font.getlength(prefix)
            lines = wrap_text(item.summary, body_font, available_width)
            if not lines:
                continue
            draw.text((x, y), f"{prefix}{lines[0]}", font=body_font, fill=0)
            y += body_font.size + self.line_spacing
            for line in lines[1:]:
                draw.text((x + body_font.getlength(prefix), y), line, font=body_font, fill=0)
                y += body_font.size + self.line_spacing
            if y > max_height:
                break

        return y

    def _render_weather(self, draw: ImageDraw.ImageDraw, x: int, y: int, max_width: int) -> int:
        title_font = load_font(self.font_path, self.header_font_size - 6)
        body_font = load_font(self.font_path, self.font_size)

        draw.text((x, y), "Weather", font=title_font, fill=0)
        y += title_font.size + self.line_spacing

        try:
            weather = self.weather_provider.fetch_weather()
            description = self.weather_provider.describe_code(weather.weather_code)
            temp_line = f"{weather.temperature_c:.1f}°C" if weather.temperature_c is not None else "--"
            hi = f"{weather.temp_max_c:.1f}°C" if weather.temp_max_c is not None else "--"
            lo = f"{weather.temp_min_c:.1f}°C" if weather.temp_min_c is not None else "--"

            draw.text((x, y), f"Now: {temp_line}", font=body_font, fill=0)
            y += body_font.size + self.line_spacing
            draw.text((x, y), f"High: {hi} / Low: {lo}", font=body_font, fill=0)
            y += body_font.size + self.line_spacing

            lines = wrap_text(description, body_font, max_width)
            y = draw_text_lines(draw, lines, (x, y), body_font, 0, self.line_spacing)
        except Exception as exc:
            logger.warning("Weather fetch failed: %s", exc)
            draw.text((x, y), "Weather unavailable", font=body_font, fill=0)
            y += body_font.size + self.line_spacing

        return y

    def build_frame(self) -> Image.Image:
        width = self.display_config.get("width", 800)
        height = self.display_config.get("height", 480)
        canvas = Image.new("L", (width, height), color=255)
        draw = ImageDraw.Draw(canvas)

        margin = 24
        y = margin
        y = self._render_header(draw, width, y)

        reminders = self.reminders_provider.fetch_reminders()
        column_gap = 32
        column_width = (width - margin * 2 - column_gap) // 2
        column_height = height - y - margin

        reminders_x = margin
        weather_x = margin + column_width + column_gap

        self._render_reminders(draw, reminders, reminders_x, y, column_width, y + column_height)
        self._render_weather(draw, weather_x, y, column_width)

        return canvas

    def refresh_display(self) -> bool:
        logger.info("Starting dashboard refresh...")
        frame = self.build_frame()

        if self.test_mode:
            output_path = "dashboard_preview.png"
            frame.save(output_path)
            logger.info("Test mode: Saved output to %s", output_path)
            return True

        if self.epd is None:
            raise RuntimeError("E-ink display not initialized")

        display_image = frame.convert("1")
        buffer = self.epd.getbuffer(display_image)
        self.epd.display(buffer)
        logger.info("Display updated successfully")
        return True

    def cleanup(self) -> None:
        if self.epd is not None:
            try:
                logger.info("Putting display to sleep...")
                self.epd.sleep()
            except Exception as exc:
                logger.error("Error during cleanup: %s", exc)


def main() -> None:
    parser = argparse.ArgumentParser(description="E-ink Dashboard")
    parser.add_argument("--test-mode", action="store_true", help="Save output to a file")
    parser.add_argument("--config", default="config.yaml", help="Path to config file")

    args = parser.parse_args()

    try:
        dashboard = Dashboard(config_path=args.config, test_mode=args.test_mode)
        success = dashboard.refresh_display()
        dashboard.cleanup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logger.info("Interrupted by user")
        sys.exit(1)
    except Exception as exc:
        logger.error("Fatal error: %s", exc, exc_info=True)
        sys.exit(1)


if __name__ == "__main__":
    main()
