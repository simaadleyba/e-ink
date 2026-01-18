#!/usr/bin/env python3
"""
Manul Scraper Module
- Uses fixed allow-list from manul_urls.py (no crawling / guessing)
- Reads YAML config (because manul_display passes config_path)
- Returns a ManulData object with .image/.name/.location/.description
"""

import logging
import random
import re
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import requests
import yaml
from PIL import Image

from manul_urls import MANUL_URLS

logger = logging.getLogger(__name__)


@dataclass
class ManulData:
    name: str
    location: str
    description: str
    image: Optional[Image.Image]
    source_url: str


class ManulScraper:
    def __init__(self, config_path_or_dict: Union[str, Path, dict]):
        # manul_display passes a YAML path, so support that
        if isinstance(config_path_or_dict, (str, Path)):
            cfg_path = Path(config_path_or_dict)
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        elif isinstance(config_path_or_dict, dict):
            cfg = config_path_or_dict
        else:
            raise TypeError(f"Expected config path or dict, got {type(config_path_or_dict)}")

        # Optional scraping settings (safe defaults if not in YAML)
        scraping = cfg.get("scraping", {}) if isinstance(cfg, dict) else {}
        manuls_scraping = scraping.get("manuls", {}) if isinstance(scraping, dict) else {}

        self.user_agent = manuls_scraping.get("user_agent", "manul/1.0 (+https://manulization.com)")
        self.timeout = manuls_scraping.get("timeout", 20)
        self.retry_attempts = manuls_scraping.get("retry_attempts", 3)
        self.retry_delay = manuls_scraping.get("retry_delay", 2)

        self.manul_urls = list(dict.fromkeys(MANUL_URLS))
        if not self.manul_urls:
            raise RuntimeError("MANUL_URLS is empty – nothing to scrape")

        self.session = requests.Session()
        self.session.headers.update({"User-Agent": self.user_agent})

    def _get(self, url: str) -> Optional[requests.Response]:
        for attempt in range(1, self.retry_attempts + 1):
            try:
                r = self.session.get(url, timeout=self.timeout)
                r.raise_for_status()
                return r
            except Exception as e:
                logger.warning(f"GET failed ({attempt}/{self.retry_attempts}) for {url}: {e}")
                if attempt < self.retry_attempts:
                    import time
                    time.sleep(self.retry_delay)
        return None

    @staticmethod
    def _extract_meta(html: str, property_name: str) -> Optional[str]:
        """
        Extract <meta property="og:..." content="..."> style values.
        Works even without BeautifulSoup.
        """
        # property="og:image" content="..."
        pattern = rf'<meta[^>]+property=["\']{re.escape(property_name)}["\'][^>]*content=["\']([^"\']+)["\']'
        m = re.search(pattern, html, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    @staticmethod
    def _extract_title(html: str) -> Optional[str]:
        # Prefer og:title
        ogt = ManulScraper._extract_meta(html, "og:title")
        if ogt:
            return ogt

        # Fallback <title>...</title>
        m = re.search(r"<title>\s*(.*?)\s*</title>", html, flags=re.IGNORECASE | re.DOTALL)
        if m:
            return re.sub(r"\s+", " ", m.group(1)).strip()
        return None

    @staticmethod
    def _extract_first_img_src(html: str) -> Optional[str]:
        # crude fallback: first <img ... src="...">
        m = re.search(r'<img[^>]+src=["\']([^"\']+)["\']', html, flags=re.IGNORECASE)
        if m:
            return m.group(1).strip()
        return None

    def _download_image(self, img_url: str) -> Optional[Image.Image]:
        r = self._get(img_url)
        if r is None:
            return None
        try:
            im = Image.open(BytesIO(r.content))
            im.load()
            return im
        except Exception as e:
            logger.warning(f"Failed to decode image {img_url}: {e}")
            return None

    def get_random_manul(self) -> Optional[ManulData]:
        url = random.choice(self.manul_urls)
        logger.info(f"Selected manul URL: {url}")

        page = self._get(url)
        if page is None:
            logger.error(f"Failed to fetch manul page: {url}")
            return None

        html = page.text

        # 1) image URL
        img_url = self._extract_meta(html, "og:image") or self._extract_first_img_src(html)
        if img_url and img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url and img_url.startswith("/"):
            img_url = "https://manulization.com" + img_url

        # 2) title/name
        title = self._extract_title(html) or "Unknown Manul"
        # try to sanitize "X – Manulization" style titles
        name = re.split(r"\s[-–|]\s", title)[0].strip() if title else "Unknown Manul"

        # 3) description (optional)
        desc = self._extract_meta(html, "og:description")
        if not desc:
            # fallback meta name="description"
            m = re.search(r'<meta[^>]+name=["\']description["\'][^>]*content=["\']([^"\']+)["\']',
                          html, flags=re.IGNORECASE)
            desc = m.group(1).strip() if m else ""

        # 4) location (we can’t reliably parse without knowing page structure; keep blank for now)
        location = ""

        image = self._download_image(img_url) if img_url else None

        return ManulData(
            name=name,
            location=location,
            description=desc or "",
            image=image,
            source_url=url,
        )


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = ManulScraper("config.yaml")
    m = scraper.get_random_manul()
    if m and m.image:
        print("OK:", m.name, "img=", m.image.size, "url=", m.source_url)
    else:
        print("Failed")
