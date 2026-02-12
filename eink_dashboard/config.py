"""Configuration loading for the e-ink dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

import yaml


@dataclass(frozen=True)
class DisplayConfig:
    width: int
    height: int
    model: str


@dataclass(frozen=True)
class FontConfig:
    paths: tuple[str, ...]
    time_size: int
    secondary_size: int
    quote_size: int
    sidebar_size: int


@dataclass(frozen=True)
class MapConfig:
    latitude: float
    longitude: float
    zoom: int
    render_scale: int
    tile_url_template: str
    api_key: str | None
    cache_ttl_hours: int
    timeout_seconds: int
    location_label: str


@dataclass(frozen=True)
class TimeConfig:
    local_timezone: str
    hong_kong_timezone: str
    boston_timezone: str


@dataclass(frozen=True)
class QuoteConfig:
    source: str
    quotes_file: str
    daily_seed: int


@dataclass(frozen=True)
class LayoutConfig:
    outer_margin: int
    sidebar_width: int
    separator_width: int
    map_margin: int


@dataclass(frozen=True)
class DashboardConfig:
    display: DisplayConfig
    fonts: FontConfig
    map: MapConfig
    time: TimeConfig
    quote: QuoteConfig
    layout: LayoutConfig
    cache_dir: str


DEFAULT_FONT_PATHS = (
    "/usr/share/fonts/truetype/ibm-plex/IBMPlexMono-Regular.ttf",
    "/usr/share/fonts/truetype/google/GoogleSansMono-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)


def _default_local_timezone() -> str:
    tzinfo = datetime.now().astimezone().tzinfo
    if tzinfo is None:
        return "UTC"
    key = getattr(tzinfo, "key", None)
    if isinstance(key, str) and key:
        return key
    name = str(tzinfo)
    return name if name else "UTC"


def _as_tuple(values: list[str] | tuple[str, ...] | None) -> tuple[str, ...]:
    if not values:
        return DEFAULT_FONT_PATHS
    return tuple(str(item) for item in values)


def load_config(path: Path) -> DashboardConfig:
    payload = yaml.safe_load(path.read_text(encoding="utf-8")) or {}

    display = payload.get("display", {})
    fonts = payload.get("fonts", {})
    map_cfg = payload.get("map", {})
    time_cfg = payload.get("timezones", {})
    quote_cfg = payload.get("quotes", {})
    layout_cfg = payload.get("layout", {})

    return DashboardConfig(
        display=DisplayConfig(
            width=int(display.get("width", 800)),
            height=int(display.get("height", 480)),
            model=str(display.get("model", "epd7in5_V2")),
        ),
        fonts=FontConfig(
            paths=_as_tuple(fonts.get("paths")),
            time_size=int(fonts.get("time_size", 118)),
            secondary_size=int(fonts.get("secondary_size", 28)),
            quote_size=int(fonts.get("quote_size", 24)),
            sidebar_size=int(fonts.get("sidebar_size", 20)),
        ),
        map=MapConfig(
            latitude=float(map_cfg.get("latitude", 42.3601)),
            longitude=float(map_cfg.get("longitude", -71.0589)),
            zoom=int(map_cfg.get("zoom", 14)),
            render_scale=int(map_cfg.get("render_scale", 2)),
            tile_url_template=str(
                map_cfg.get(
                    "tile_url_template",
                    "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}.png",
                )
            ),
            api_key=map_cfg.get("api_key") or None,
            cache_ttl_hours=int(map_cfg.get("cache_ttl_hours", 24)),
            timeout_seconds=int(map_cfg.get("timeout_seconds", 12)),
            location_label=str(map_cfg.get("location_label", "LOCAL MAP")),
        ),
        time=TimeConfig(
            local_timezone=str(time_cfg.get("local", _default_local_timezone())),
            hong_kong_timezone=str(time_cfg.get("hong_kong", "Asia/Hong_Kong")),
            boston_timezone=str(time_cfg.get("boston", "America/New_York")),
        ),
        quote=QuoteConfig(
            source=str(quote_cfg.get("source", "local_json")),
            quotes_file=str(quote_cfg.get("quotes_file", "eink_dashboard/assets/quotes.json")),
            daily_seed=int(quote_cfg.get("daily_seed", 0)),
        ),
        layout=LayoutConfig(
            outer_margin=int(layout_cfg.get("outer_margin", 22)),
            sidebar_width=int(layout_cfg.get("sidebar_width", 278)),
            separator_width=int(layout_cfg.get("separator_width", 2)),
            map_margin=int(layout_cfg.get("map_margin", 18)),
        ),
        cache_dir=str(payload.get("cache_dir", "cache")),
    )
