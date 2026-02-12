"""Configuration loading for the e-ink dashboard."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from pathlib import Path


@dataclass(frozen=True)
class DisplayConfig:
    width: int
    height: int
    model: str


@dataclass(frozen=True)
class FontConfig:
    light_paths: tuple[str, ...]
    regular_paths: tuple[str, ...]
    medium_paths: tuple[str, ...]
    italic_paths: tuple[str, ...]
    local_time_size: int
    local_ampm_size: int
    date_size: int
    world_label_size: int
    world_time_size: int
    world_ampm_size: int
    quote_size: int
    quote_author_size: int
    map_label_size: int
    map_coords_size: int


@dataclass(frozen=True)
class MapConfig:
    zoom: int
    render_scale: int
    tile_url_template: str
    api_key: str | None
    cache_ttl_hours: int
    timeout_seconds: int
    user_agent: str


@dataclass(frozen=True)
class MapCity:
    name: str
    latitude: float
    longitude: float


@dataclass(frozen=True)
class TimeConfig:
    local_timezone: str
    hong_kong_timezone: str
    boston_timezone: str
    seattle_timezone: str


@dataclass(frozen=True)
class QuoteConfig:
    source: str
    quotes_file: str
    daily_seed: int


@dataclass(frozen=True)
class LayoutConfig:
    sidebar_width: int
    sidebar_padding: int
    divider_length: int
    divider_thickness: int
    world_block_gap: int
    quote_bottom_padding: int
    map_label_margin: int


@dataclass(frozen=True)
class DashboardConfig:
    display: DisplayConfig
    fonts: FontConfig
    map: MapConfig
    map_cities: tuple[MapCity, ...]
    time: TimeConfig
    quote: QuoteConfig
    layout: LayoutConfig
    cache_dir: str


DEFAULT_LIGHT_PATHS = (
    "fonts/Montserrat-Light.ttf",
    "fonts/Montserrat-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

DEFAULT_REGULAR_PATHS = (
    "fonts/Montserrat-Regular.ttf",
    "fonts/Montserrat-Medium.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

DEFAULT_MEDIUM_PATHS = (
    "fonts/Montserrat-Medium.ttf",
    "fonts/Montserrat-SemiBold.ttf",
    "fonts/Montserrat-Regular.ttf",
    "/usr/share/fonts/truetype/dejavu/DejaVuSansMono.ttf",
)

DEFAULT_ITALIC_PATHS = (
    "fonts/Montserrat-LightItalic.ttf",
    "fonts/Montserrat-Italic.ttf",
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


def _as_tuple(values: list[str] | tuple[str, ...] | None, fallback: tuple[str, ...]) -> tuple[str, ...]:
    if not values:
        return fallback
    return tuple(str(item) for item in values)


def load_config(path: Path) -> DashboardConfig:
    import yaml

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
            light_paths=_as_tuple(fonts.get("light_paths"), DEFAULT_LIGHT_PATHS),
            regular_paths=_as_tuple(fonts.get("regular_paths"), DEFAULT_REGULAR_PATHS),
            medium_paths=_as_tuple(fonts.get("medium_paths"), DEFAULT_MEDIUM_PATHS),
            italic_paths=_as_tuple(fonts.get("italic_paths"), DEFAULT_ITALIC_PATHS),
            local_time_size=int(fonts.get("local_time_size", 36)),
            local_ampm_size=int(fonts.get("local_ampm_size", 9)),
            date_size=int(fonts.get("date_size", 8)),
            world_label_size=int(fonts.get("world_label_size", 7)),
            world_time_size=int(fonts.get("world_time_size", 18)),
            world_ampm_size=int(fonts.get("world_ampm_size", 9)),
            quote_size=int(fonts.get("quote_size", 9)),
            quote_author_size=int(fonts.get("quote_author_size", 7)),
            map_label_size=int(fonts.get("map_label_size", 12)),
            map_coords_size=int(fonts.get("map_coords_size", 10)),
        ),
        map=MapConfig(
            zoom=int(map_cfg.get("zoom", 16)),
            render_scale=int(map_cfg.get("render_scale", 2)),
            tile_url_template=str(
                map_cfg.get(
                    "tile_url_template",
                    "https://tiles.stadiamaps.com/tiles/stamen_toner/{z}/{x}/{y}@2x.png",
                )
            ),
            api_key=map_cfg.get("api_key") or None,
            cache_ttl_hours=int(map_cfg.get("cache_ttl_hours", 24)),
            timeout_seconds=int(map_cfg.get("timeout_seconds", 12)),
            user_agent=str(
                map_cfg.get("user_agent", "eink-dashboard/1.0 (+https://github.com/)")
            ),
        ),
        map_cities=tuple(
            MapCity(
                name=str(row.get("name", "Unknown")).strip() or "Unknown",
                latitude=float(row.get("latitude")),
                longitude=float(row.get("longitude")),
            )
            for row in payload.get("map_cities", [])
            if row.get("latitude") is not None and row.get("longitude") is not None
        ),
        time=TimeConfig(
            local_timezone=str(time_cfg.get("local", "Europe/Istanbul")),
            hong_kong_timezone=str(time_cfg.get("hong_kong", "Asia/Hong_Kong")),
            boston_timezone=str(time_cfg.get("boston", "America/New_York")),
            seattle_timezone=str(time_cfg.get("seattle", "America/Los_Angeles")),
        ),
        quote=QuoteConfig(
            source=str(quote_cfg.get("source", "local_json")),
            quotes_file=str(quote_cfg.get("quotes_file", "assets/quotes.json")),
            daily_seed=int(quote_cfg.get("daily_seed", 0)),
        ),
        layout=LayoutConfig(
            sidebar_width=int(layout_cfg.get("sidebar_width", 160)),
            sidebar_padding=int(layout_cfg.get("sidebar_padding", 24)),
            divider_length=int(layout_cfg.get("divider_length", 48)),
            divider_thickness=int(layout_cfg.get("divider_thickness", 1)),
            world_block_gap=int(layout_cfg.get("world_block_gap", 18)),
            quote_bottom_padding=int(layout_cfg.get("quote_bottom_padding", 22)),
            map_label_margin=int(layout_cfg.get("map_label_margin", 12)),
        ),
        cache_dir=str(payload.get("cache_dir", "cache")),
    )
