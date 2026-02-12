"""Stadia map tile provider with local caching."""

from __future__ import annotations

import logging
import math
from datetime import datetime, timedelta
from pathlib import Path

import requests
from PIL import Image, ImageDraw

from eink_dashboard.config import MapConfig

logger = logging.getLogger(__name__)


class MapProvider:
    """Render a high-detail map crop around a configured lat/lon."""

    TILE_SIZE = 256

    def __init__(self, config: MapConfig, cache_root: Path):
        self.config = config
        self.cache_root = cache_root / "map_tiles"
        self.cache_root.mkdir(parents=True, exist_ok=True)

    def get_map(self, width: int, height: int) -> Image.Image:
        render_scale = max(1, self.config.render_scale)
        source_width = width * render_scale
        source_height = height * render_scale
        # Extra zoom preserves detail before downsampling to e-ink resolution.
        zoom = min(19, self.config.zoom + (1 if render_scale > 1 else 0))

        try:
            map_img = self._render_viewport(
                lat=self.config.latitude,
                lon=self.config.longitude,
                zoom=zoom,
                width=source_width,
                height=source_height,
            )
        except Exception as exc:  # noqa: BLE001
            logger.warning("Map rendering failed, using fallback tile: %s", exc)
            map_img = self._fallback_image(source_width, source_height)

        if render_scale > 1:
            map_img = map_img.resize((width, height), Image.Resampling.LANCZOS)

        return self._high_contrast(map_img)

    def _render_viewport(self, lat: float, lon: float, zoom: int, width: int, height: int) -> Image.Image:
        world_size = self.TILE_SIZE * (2**zoom)
        center_x, center_y = self._lat_lon_to_world(lat, lon, world_size)

        left = center_x - (width / 2)
        top = center_y - (height / 2)

        min_tile_x = math.floor(left / self.TILE_SIZE)
        min_tile_y = math.floor(top / self.TILE_SIZE)
        max_tile_x = math.floor((left + width - 1) / self.TILE_SIZE)
        max_tile_y = math.floor((top + height - 1) / self.TILE_SIZE)

        mosaic_width = (max_tile_x - min_tile_x + 1) * self.TILE_SIZE
        mosaic_height = (max_tile_y - min_tile_y + 1) * self.TILE_SIZE
        mosaic = Image.new("L", (mosaic_width, mosaic_height), color=255)

        tiles_per_axis = 2**zoom

        for tile_x in range(min_tile_x, max_tile_x + 1):
            for tile_y in range(min_tile_y, max_tile_y + 1):
                wrapped_x = tile_x % tiles_per_axis
                clamped_y = max(0, min(tile_y, tiles_per_axis - 1))
                tile = self._load_tile(zoom, wrapped_x, clamped_y)
                paste_x = (tile_x - min_tile_x) * self.TILE_SIZE
                paste_y = (tile_y - min_tile_y) * self.TILE_SIZE
                mosaic.paste(tile, (paste_x, paste_y))

        crop_x = int(left - (min_tile_x * self.TILE_SIZE))
        crop_y = int(top - (min_tile_y * self.TILE_SIZE))
        return mosaic.crop((crop_x, crop_y, crop_x + width, crop_y + height))

    def _load_tile(self, zoom: int, tile_x: int, tile_y: int) -> Image.Image:
        tile_path = self.cache_root / str(zoom) / str(tile_x) / f"{tile_y}.png"
        tile_path.parent.mkdir(parents=True, exist_ok=True)

        if tile_path.exists() and self._is_cache_fresh(tile_path):
            return self._read_tile(tile_path)

        url = self.config.tile_url_template.format(z=zoom, x=tile_x, y=tile_y)
        params: dict[str, str] = {}
        if self.config.api_key:
            params["api_key"] = self.config.api_key

        try:
            response = requests.get(url, params=params or None, timeout=self.config.timeout_seconds)
            response.raise_for_status()
            tile_path.write_bytes(response.content)
            return self._read_tile(tile_path)
        except Exception as exc:  # noqa: BLE001
            logger.debug("Tile download failed for z%s/%s/%s: %s", zoom, tile_x, tile_y, exc)
            if tile_path.exists():
                return self._read_tile(tile_path)
            return self._missing_tile()

    def _is_cache_fresh(self, path: Path) -> bool:
        ttl = timedelta(hours=max(1, self.config.cache_ttl_hours))
        modified_at = datetime.fromtimestamp(path.stat().st_mtime)
        return datetime.now() - modified_at <= ttl

    def _lat_lon_to_world(self, lat: float, lon: float, world_size: int) -> tuple[float, float]:
        clamped_lat = max(min(lat, 85.05112878), -85.05112878)
        x = (lon + 180.0) / 360.0 * world_size
        lat_rad = math.radians(clamped_lat)
        mercator = math.log(math.tan((math.pi / 4.0) + (lat_rad / 2.0)))
        y = (1.0 - (mercator / math.pi)) / 2.0 * world_size
        return x, y

    def _high_contrast(self, image: Image.Image) -> Image.Image:
        return image.convert("L").point(lambda px: 0 if px < 180 else 255, mode="1").convert("L")

    def _missing_tile(self) -> Image.Image:
        tile = Image.new("L", (self.TILE_SIZE, self.TILE_SIZE), 255)
        draw = ImageDraw.Draw(tile)
        draw.rectangle((0, 0, self.TILE_SIZE - 1, self.TILE_SIZE - 1), outline=0, width=2)
        draw.line((0, 0, self.TILE_SIZE - 1, self.TILE_SIZE - 1), fill=0, width=2)
        draw.line((self.TILE_SIZE - 1, 0, 0, self.TILE_SIZE - 1), fill=0, width=2)
        return tile

    def _fallback_image(self, width: int, height: int) -> Image.Image:
        fallback = Image.new("L", (width, height), 255)
        draw = ImageDraw.Draw(fallback)
        draw.rectangle((0, 0, width - 1, height - 1), outline=0, width=3)
        draw.line((0, 0, width - 1, height - 1), fill=0, width=3)
        draw.line((width - 1, 0, 0, height - 1), fill=0, width=3)
        return fallback

    def _read_tile(self, path: Path) -> Image.Image:
        with Image.open(path) as tile:
            return tile.convert("L")
