#!/usr/bin/env python3
"""Rendering utilities for the e-ink dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Iterable, List, Tuple

from PIL import ImageDraw, ImageFont


@dataclass(frozen=True)
class TextBlock:
    text: str
    font: ImageFont.FreeTypeFont
    fill: int
    line_spacing: int


def load_font(font_path: str, size: int) -> ImageFont.FreeTypeFont:
    """Load a font, falling back to DejaVu Sans Mono if needed."""
    try:
        return ImageFont.truetype(font_path, size)
    except OSError:
        return ImageFont.truetype(
            "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
            size,
        )


def wrap_text(text: str, font: ImageFont.FreeTypeFont, max_width: int) -> List[str]:
    """Wrap text to fit within max_width using font metrics."""
    words = text.split()
    lines: List[str] = []
    current: List[str] = []

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

    if not lines:
        return [""]
    return lines


def draw_text_lines(
    draw: ImageDraw.ImageDraw,
    lines: Iterable[str],
    position: Tuple[int, int],
    font: ImageFont.FreeTypeFont,
    fill: int,
    line_spacing: int,
) -> int:
    """Draw lines of text and return the final y position."""
    x, y = position
    for line in lines:
        draw.text((x, y), line, font=font, fill=fill)
        y += font.size + line_spacing
    return y
