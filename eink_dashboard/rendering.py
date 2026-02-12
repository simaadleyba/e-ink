"""Rendering logic for the e-ink dashboard visual layout."""

from __future__ import annotations

from datetime import datetime

from PIL import Image, ImageDraw, ImageFont

from eink_dashboard.config import DashboardConfig
from eink_dashboard.providers.quote_provider import Quote


class DashboardRenderer:
    """Compose the dashboard image in strict black and white."""

    def __init__(self, config: DashboardConfig):
        self.config = config

        self.local_time_font = self._load_font(config.fonts.light_paths, config.fonts.local_time_size + 4)
        self.local_ampm_font = self._load_font(config.fonts.medium_paths, config.fonts.local_ampm_size + 3)
        self.date_font = self._load_font(config.fonts.light_paths, config.fonts.date_size + 1)
        self.world_label_font = self._load_font(config.fonts.medium_paths, config.fonts.world_label_size + 1)
        self.world_time_font = self._load_font(config.fonts.regular_paths, config.fonts.world_time_size + 2)
        self.world_ampm_font = self._load_font(config.fonts.medium_paths, config.fonts.world_ampm_size + 3)
        self.quote_font = self._load_font(config.fonts.italic_paths, config.fonts.quote_size + 1)
        self.quote_author_font = self._load_font(config.fonts.medium_paths, config.fonts.quote_author_size + 1)
        self.map_label_font = self._load_font(config.fonts.medium_paths, config.fonts.map_label_size)
        self.map_coords_font = self._load_font(config.fonts.regular_paths, config.fonts.map_coords_size)

    def render(
        self,
        local_time: datetime,
        hong_kong_time: datetime,
        boston_time: datetime,
        seattle_time: datetime,
        quote: Quote,
        map_image: Image.Image,
        map_city_name: str,
        map_city_latitude: float,
        map_city_longitude: float,
    ) -> Image.Image:
        width = self.config.display.width
        height = self.config.display.height
        sidebar_width = self.config.layout.sidebar_width

        canvas = Image.new("L", (width, height), color=255)
        draw = ImageDraw.Draw(canvas)

        draw.rectangle((0, 0, sidebar_width - 1, height - 1), fill=0)

        map_width = width - sidebar_width
        map_height = height
        map_for_display = map_image.resize((map_width, map_height), Image.Resampling.LANCZOS)
        canvas.paste(map_for_display, (sidebar_width, 0))

        self._draw_left_panel(draw, local_time, hong_kong_time, boston_time, seattle_time, quote, height)
        self._draw_map_overlays(
            draw=draw,
            width=width,
            height=height,
            map_x=sidebar_width,
            city_name=map_city_name,
            city_latitude=map_city_latitude,
            city_longitude=map_city_longitude,
        )

        return canvas

    def _draw_left_panel(
        self,
        draw: ImageDraw.ImageDraw,
        local_time: datetime,
        hong_kong_time: datetime,
        boston_time: datetime,
        seattle_time: datetime,
        quote: Quote,
        panel_height: int,
    ) -> None:
        primary_color = 255
        secondary_color = 136
        pad = self.config.layout.sidebar_padding
        x = pad
        y = 38
        clock_to_date_gap = 20
        date_to_divider_gap = 24
        divider_to_first_clock_gap = 32
        city_to_time_gap = 11
        world_row_gap = self.config.layout.world_block_gap + 14

        y = self._draw_time_with_ampm(
            draw=draw,
            x=x,
            y=y,
            time_dt=local_time,
            big_font=self.local_time_font,
            ampm_font=self.local_ampm_font,
            fill=primary_color,
            ampm_fill=secondary_color,
        )

        y += clock_to_date_gap
        date_day = local_time.strftime("%a").upper()
        date_value = local_time.strftime("%b %d").upper()
        date_text = f"{date_day},  {date_value}"
        self._draw_tracked_text(draw, x, y, date_text, self.date_font, fill=secondary_color, tracking=1)
        y += self._font_pixel_height(self.date_font)

        y += date_to_divider_gap
        divider_end = x + self.config.layout.divider_length
        draw.line(
            (x, y, divider_end, y),
            fill=255,
            width=max(1, self.config.layout.divider_thickness),
        )

        y += divider_to_first_clock_gap
        for city, dt in (
            ("HONG KONG", hong_kong_time),
            ("BOSTON", boston_time),
            ("SEATTLE", seattle_time),
        ):
            self._draw_tracked_text(draw, x, y, city, self.world_label_font, fill=secondary_color, tracking=2)
            y += self._font_pixel_height(self.world_label_font) + city_to_time_gap
            y = self._draw_time_with_ampm(
                draw=draw,
                x=x,
                y=y,
                time_dt=dt,
                big_font=self.world_time_font,
                ampm_font=self.world_ampm_font,
                fill=primary_color,
                ampm_fill=secondary_color,
            )
            y += world_row_gap

        quote_body = f'"{quote.text}"'
        quote_right_padding = 12
        max_quote_width = self.config.layout.sidebar_width - (pad * 2) - quote_right_padding
        quote_line_height = self._font_pixel_height(self.quote_font) + 3
        author_text = f"- {quote.author.upper()}"
        author_height = self._text_height(draw, author_text, self.quote_author_font)
        author_gap = 4

        min_quote_top = y + 20
        available_height = panel_height - self.config.layout.quote_bottom_padding - min_quote_top
        if available_height < (author_height + author_gap + quote_line_height):
            return

        max_lines = 3
        min_block_two_lines = (quote_line_height * 2) + author_gap + author_height
        if available_height < min_block_two_lines:
            max_lines = 1
        elif available_height < ((quote_line_height * 3) + author_gap + author_height):
            max_lines = 2

        quote_lines = self._wrap_text(
            text=quote_body,
            font=self.quote_font,
            max_width=max_quote_width,
            max_lines=max_lines,
        )
        if len(quote_lines) > 3:
            quote_lines = quote_lines[:3]

        quote_block_height = len(quote_lines) * quote_line_height + author_gap + author_height
        quote_top = max(min_quote_top, panel_height - self.config.layout.quote_bottom_padding - quote_block_height)

        for line in quote_lines:
            draw.text((x, quote_top), line, font=self.quote_font, fill=primary_color)
            quote_top += quote_line_height

        quote_top += author_gap
        self._draw_tracked_text(
            draw,
            x,
            quote_top,
            author_text,
            self.quote_author_font,
            fill=secondary_color,
            tracking=1,
        )

    def _draw_map_overlays(
        self,
        draw: ImageDraw.ImageDraw,
        width: int,
        height: int,
        map_x: int,
        city_name: str,
        city_latitude: float,
        city_longitude: float,
    ) -> None:
        map_width = width - map_x
        pin_x = map_x + (map_width // 2)
        pin_y = height // 2

        outer = 9
        inner = 3

        draw.ellipse((pin_x - outer - 1, pin_y - outer - 1, pin_x + outer + 1, pin_y + outer + 1), fill=255)
        draw.ellipse((pin_x - outer, pin_y - outer, pin_x + outer, pin_y + outer), outline=0, width=2)
        draw.ellipse((pin_x - inner, pin_y - inner, pin_x + inner, pin_y + inner), fill=0)

        city_text = self._spaced_caps(city_name)
        coords_text = self._format_coords(city_latitude, city_longitude)

        city_bbox = draw.textbbox((0, 0), city_text, font=self.map_label_font)
        coords_bbox = draw.textbbox((0, 0), coords_text, font=self.map_coords_font)

        text_width = max(city_bbox[2] - city_bbox[0], coords_bbox[2] - coords_bbox[0])
        text_height = (city_bbox[3] - city_bbox[1]) + 6 + (coords_bbox[3] - coords_bbox[1])

        pad_x = 10
        pad_y = 8
        margin = self.config.layout.map_label_margin

        box_right = width - margin
        box_bottom = height - margin
        box_left = box_right - text_width - (pad_x * 2)
        box_top = box_bottom - text_height - (pad_y * 2)

        draw.rectangle((box_left, box_top, box_right, box_bottom), fill=255)

        text_x = box_left + pad_x
        text_y = box_top + pad_y
        draw.text((text_x, text_y), city_text, font=self.map_label_font, fill=0)
        text_y += (city_bbox[3] - city_bbox[1]) + 6
        self._draw_tracked_text(draw, text_x, text_y, coords_text, self.map_coords_font, fill=0, tracking=1)

    def _draw_time_with_ampm(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        time_dt: datetime,
        big_font: ImageFont.FreeTypeFont,
        ampm_font: ImageFont.FreeTypeFont,
        fill: int,
        ampm_fill: int,
    ) -> int:
        time_text = time_dt.strftime("%I:%M").lstrip("0") or "12:00"
        ampm_text = time_dt.strftime("%p")

        draw.text((x, y), time_text, font=big_font, fill=fill)

        time_bbox = draw.textbbox((0, 0), time_text, font=big_font)
        time_width = time_bbox[2] - time_bbox[0]
        time_height = time_bbox[3] - time_bbox[1]

        ampm_bbox = draw.textbbox((0, 0), ampm_text, font=ampm_font)
        ampm_height = ampm_bbox[3] - ampm_bbox[1]

        ampm_x = x + time_width + 7
        ampm_y = y + max(0, time_height - ampm_height - 1)
        draw.text((ampm_x, ampm_y), ampm_text, font=ampm_font, fill=ampm_fill)

        return y + time_height

    def _wrap_text(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
        max_lines: int,
    ) -> list[str]:
        words = text.split()
        lines: list[str] = []
        index = 0

        while index < len(words) and len(lines) < max_lines:
            current = words[index]
            index += 1
            while index < len(words):
                candidate = f"{current} {words[index]}"
                if font.getlength(candidate) <= max_width:
                    current = candidate
                    index += 1
                else:
                    break
            lines.append(current)

        if words and not lines:
            return [text[: max(1, max_width // 8)]]

        if index < len(words) and lines:
            lines[-1] = self._truncate_with_ellipsis(lines[-1], font, max_width)

        return lines

    def _draw_tracked_text(
        self,
        draw: ImageDraw.ImageDraw,
        x: int,
        y: int,
        text: str,
        font: ImageFont.FreeTypeFont,
        fill: int,
        tracking: int,
    ) -> None:
        current_x = float(x)
        for ch in text:
            draw.text((int(round(current_x)), y), ch, font=font, fill=fill)
            current_x += font.getlength(ch) + tracking

    def _load_font(self, paths: tuple[str, ...], size: int) -> ImageFont.FreeTypeFont:
        for path in paths:
            try:
                return ImageFont.truetype(path, size)
            except OSError:
                continue
        return ImageFont.load_default()

    def _text_height(self, draw: ImageDraw.ImageDraw, text: str, font: ImageFont.FreeTypeFont) -> int:
        bbox = draw.textbbox((0, 0), text, font=font)
        return bbox[3] - bbox[1]

    def _font_pixel_height(self, font: ImageFont.FreeTypeFont) -> int:
        ascent, descent = font.getmetrics()
        return ascent + descent

    def _spaced_caps(self, text: str) -> str:
        chars: list[str] = []
        for idx, ch in enumerate(text.upper()):
            chars.append(ch)
            if ch != " " and idx != len(text) - 1:
                chars.append(" ")
        return "".join(chars).replace("   ", "  ")

    def _format_coords(self, lat: float, lon: float) -> str:
        lat_suffix = "N" if lat >= 0 else "S"
        lon_suffix = "E" if lon >= 0 else "W"
        return f"{abs(lat):.2f}\N{DEGREE SIGN}{lat_suffix} {abs(lon):.2f}\N{DEGREE SIGN}{lon_suffix}"

    def _truncate_with_ellipsis(
        self,
        text: str,
        font: ImageFont.FreeTypeFont,
        max_width: int,
    ) -> str:
        if font.getlength(text) <= max_width:
            return text
        ellipsis = "..."
        trimmed = text.rstrip()
        while trimmed and font.getlength(f"{trimmed}{ellipsis}") > max_width:
            trimmed = trimmed[:-1]
        return f"{trimmed.rstrip()}{ellipsis}" if trimmed else ellipsis
