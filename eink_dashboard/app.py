"""Application orchestration for preview and panel refresh."""

from __future__ import annotations

import logging
from datetime import datetime
from pathlib import Path
from zoneinfo import ZoneInfo

from PIL import Image

from eink_dashboard.config import DashboardConfig, load_config
from eink_dashboard.providers.map_provider import MapProvider
from eink_dashboard.providers.quote_provider import QuoteProvider
from eink_dashboard.rendering import DashboardRenderer

logger = logging.getLogger(__name__)


class DashboardApp:
    """Coordinates data loading, rendering, and output."""

    def __init__(self, config_path: Path):
        self.project_root = config_path.resolve().parent
        self.config: DashboardConfig = load_config(config_path)

        cache_root = (self.project_root / self.config.cache_dir).resolve()
        cache_root.mkdir(parents=True, exist_ok=True)

        self.map_provider = MapProvider(self.config.map, cache_root)
        self.quote_provider = QuoteProvider(self.config.quote, self.project_root)
        self.renderer = DashboardRenderer(self.config)

        self.epd = None

    def run(self, preview: bool, preview_path: Path) -> bool:
        frame = self._build_frame()

        if preview:
            output_path = preview_path
            if not output_path.is_absolute():
                output_path = (self.project_root / output_path).resolve()
            output_path.parent.mkdir(parents=True, exist_ok=True)
            frame.save(output_path)
            logger.info("Preview saved to %s", output_path)
            return True

        self._display_frame(frame)
        logger.info("E-ink panel updated")
        return True

    def cleanup(self) -> None:
        if self.epd is not None:
            try:
                self.epd.sleep()
            except Exception as exc:  # noqa: BLE001
                logger.warning("Failed to sleep display: %s", exc)

    def _build_frame(self) -> Image.Image:
        local_tz = self._load_timezone(self.config.time.local_timezone)
        hk_tz = self._load_timezone(self.config.time.hong_kong_timezone)
        bos_tz = self._load_timezone(self.config.time.boston_timezone)
        sea_tz = self._load_timezone(self.config.time.seattle_timezone)

        now_local = datetime.now(local_tz)
        now_hk = now_local.astimezone(hk_tz)
        now_boston = now_local.astimezone(bos_tz)
        now_seattle = now_local.astimezone(sea_tz)

        quote = self.quote_provider.get_daily_quote(now_local)

        map_size = self._map_render_size()
        map_image = self.map_provider.get_map(map_size[0], map_size[1])

        return self.renderer.render(
            local_time=now_local,
            hong_kong_time=now_hk,
            boston_time=now_boston,
            seattle_time=now_seattle,
            quote=quote,
            map_image=map_image,
        )

    def _map_render_size(self) -> tuple[int, int]:
        map_width = self.config.display.width - self.config.layout.sidebar_width
        map_height = self.config.display.height
        return map_width, map_height

    def _display_frame(self, frame: Image.Image) -> None:
        if self.epd is None:
            self.epd = self._init_epd()

        display_image = frame.convert("1")
        buffer = self.epd.getbuffer(display_image)
        self.epd.display(buffer)

    def _init_epd(self):
        model = self.config.display.model
        if model == "epd7in5_V2":
            from waveshare_epd import epd7in5_V2

            epd = epd7in5_V2.EPD()
        elif model == "epd7in5":
            from waveshare_epd import epd7in5

            epd = epd7in5.EPD()
        else:
            raise ValueError(f"Unsupported display model: {model}")

        epd.init()
        return epd

    def _load_timezone(self, name: str) -> ZoneInfo:
        try:
            return ZoneInfo(name)
        except Exception:  # noqa: BLE001
            logger.warning("Invalid timezone '%s', falling back to UTC", name)
            return ZoneInfo("UTC")
