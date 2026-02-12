"""Rendering logic for the e-ink dashboard."""

from __future__ import annotations

from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from eink_dashboard.config import DashboardConfig
from eink_dashboard.providers.quote_provider import Quote


class DashboardRenderer:
    """Compose the dashboard image in strict black and white."""

    def __init__(self, config: DashboardConfig):
        self.config = config
        self.time_font = self._load_font(config.fonts.time_size)
        self.secondary_font = self._load_font(config.fonts.secondary_size)
        self.quote_font = self._load_font(config.fonts.quote_size)
        self.sidebar_font = self._load_font(config.fonts.sidebar_size)

    def render(
        self,
        local_time: datetime,
        hong_kong_time: datetime,
        boston_time: datetime,
        quote: Quote,
        map_image: Image.Image,
    ) -> Image.Image:
        width = self.config.display.width
        height = self.config.display.height
        canvas = Image.new("L", (width, height), color=255)
        draw = ImageDraw.Draw(canvas)

        margin = self.config.layout.outer_margin
        sidebar_width = self.config.layout.sidebar_width
        separator_width = max(1, self.config.layout.separator_width)
        map_margin = self.config.layout.map_margin

        sidebar_right = sidebar_width
        draw.rectangle((sidebar_right, 0, sidebar_right + separator_width - 1, height), fill=0)

        map_box = self._map_box(height=height, sidebar_width=sidebar_width, margin=map_margin)
        map_for_display = map_image.resize(
            (map_box[2] - map_box[0], map_box[3] - map_box[1]), Image.Resampling.LANCZOS
        )
        canvas.paste(map_for_display, (map_box[0], map_box[1]))
        draw.rectangle((map_box[0], map_box[1], map_box[2] - 1, map_box[3] - 1), outline=0, width=2)

        label = self.config.map.location_label.upper()
        label_width = self.sidebar_font.getlength(label)
        label_x = int((sidebar_width - label_width) / 2)
        label_y = map_box[3] + 16
        draw.text((label_x, label_y), label, font=self.sidebar_font, fill=0)

        main_left = sidebar_right + separator_width + margin
        main_width = width - main_left - margin
        y = margin

        local_time_text = local_time.strftime("%H:%M")
        draw.text((main_left, y), local_time_text, font=self.time_font, fill=0)
        y += self.time_font.size + 10

        local_date = local_time.strftime("%A, %B %d")
        draw.text((main_left, y), local_date, font=self.secondary_font, fill=0)
        y += self.secondary_font.size + 18

        hk_line = f"Hong Kong  {hong_kong_time.strftime('%H:%M')}"
        bos_line = f"Boston     {boston_time.strftime('%H:%M')}"
        draw.text((main_left, y), hk_line, font=self.secondary_font, fill=0)
        y += self.secondary_font.size + 8
        draw.text((main_left, y), bos_line, font=self.secondary_font, fill=0)
        y += self.secondary_font.size + 20

        quote_width = main_width
        quote_lines = self._wrap_text(f'"{quote.text}"', self.quote_font, quote_width)
        for line in quote_lines:
            draw.text((main_left, y), line, font=self.quote_font, fill=0)
            y += self.quote_font.size + 8

        y += 6
        author_line = f"- {quote.author}"
        draw.text((main_left, y), author_line, font=self.secondary_font, fill=0)

        return canvas.point(lambda px: 0 if px < 180 else 255, mode="1").convert("L")

    def _load_font(self, size: int) -> ImageFont.FreeTypeFont:
        for path in self.config.fonts.paths:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _map_box(self, height: int, sidebar_width: int, margin: int) -> tuple[int, int, int, int]:
        usable = sidebar_width - (margin * 2)
        map_size = min(usable, height - (margin * 4) - self.sidebar_font.size)
        left = margin
        top = margin
        return left, top, left + map_size, top + map_size

    def _wrap_text(self, text: str, font: ImageFont.FreeTypeFont, max_width: int) -> list[str]:
        words = text.split()
        lines: list[str] = []
        current: list[str] = []

        for word in words:
            candidate = " ".join(current + [word]) if current else word
            if font.getlength(candidate) <= max_width:
                current.append(word)
            else:
                if current:
                    lines.append(" ".join(current))
                current = [word]

        if current:
            lines.append(" ".join(current))

        return lines if lines else [""]
