#!/usr/bin/env python3
"""
Manul Scraper Module
- Uses fixed allow-list from manul_urls.py (no crawling / guessing)
- Reads YAML config (because manul_display passes config_path)
- Returns a ManulData object with .image/.name/.location/.description
 - System dependency for WebP decoding: sudo apt-get install -y webp (dwebp)
"""

import logging
import random
import re
import subprocess
import tempfile
from dataclasses import dataclass
from io import BytesIO
from pathlib import Path
from typing import Optional, Union

import requests
import yaml
from bs4 import BeautifulSoup
from PIL import Image

from manul_urls import MANUL_URLS

logger = logging.getLogger(__name__)


@dataclass
class ManulData:
    name: str
    short_name: str
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
    def _extract_meta(soup: BeautifulSoup, property_name: str) -> Optional[str]:
        tag = soup.select_one(f'meta[property="{property_name}"]')
        if tag and tag.get("content"):
            return tag["content"].strip()
        return None

    @staticmethod
    def _extract_title(soup: BeautifulSoup) -> Optional[str]:
        ogt = ManulScraper._extract_meta(soup, "og:title")
        if ogt:
            return ogt
        title_tag = soup.find("title")
        if title_tag and title_tag.text:
            return re.sub(r"\s+", " ", title_tag.text).strip()
        return None

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    @staticmethod
    def _select_srcset_best(srcset: str) -> Optional[str]:
        if not srcset:
            return None
        best_url = None
        best_score = -1.0
        for candidate in srcset.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            parts = candidate.split()
            url = parts[0].strip()
            score = 0.0
            if len(parts) > 1:
                descriptor = parts[1].strip()
                if descriptor.endswith("w"):
                    try:
                        score = float(descriptor[:-1])
                    except ValueError:
                        score = 0.0
                elif descriptor.endswith("x"):
                    try:
                        score = float(descriptor[:-1])
                    except ValueError:
                        score = 0.0
            if score > best_score:
                best_score = score
                best_url = url
            if best_url is None:
                best_url = url
        return best_url

    @staticmethod
    def _decode_image(img_url: str, content: bytes, content_type: str) -> Optional[Image.Image]:
        is_webp = img_url.lower().endswith(".webp") or content_type.lower().startswith("image/webp")
        if not is_webp:
            try:
                im = Image.open(BytesIO(content))
                im.load()
                return im
            except Exception as e:
                logger.warning(f"Failed to decode image {img_url}: {e}")
                return None

        try:
            with tempfile.TemporaryDirectory() as temp_dir:
                webp_path = Path(temp_dir) / "img.webp"
                png_path = Path(temp_dir) / "img.png"
                webp_path.write_bytes(content)
                subprocess.run(
                    ["dwebp", str(webp_path), "-o", str(png_path)],
                    check=True,
                    capture_output=True,
                    text=True,
                )
                im = Image.open(png_path)
                im.load()
                return im.convert("RGB")
        except FileNotFoundError:
            logger.warning("dwebp not found. Install with: sudo apt-get install -y webp")
            return None
        except subprocess.CalledProcessError as e:
            logger.warning(f"dwebp failed for {img_url}: {e.stderr.strip()}")
            return None
        except Exception as e:
            logger.warning(f"Failed to decode WebP image {img_url}: {e}")
            return None

    def _download_image(self, img_url: str) -> Optional[Image.Image]:
        r = self._get(img_url)
        if r is None:
            return None
        content_type = r.headers.get("Content-Type", "")
        return self._decode_image(img_url, r.content, content_type)

    def get_random_manul(self) -> Optional[ManulData]:
        url = random.choice(self.manul_urls)
        logger.info(f"Selected manul URL: {url}")

        page = self._get(url)
        if page is None:
            logger.error(f"Failed to fetch manul page: {url}")
            return None

        html = page.text
        soup = BeautifulSoup(html, "html.parser")

        # 1) image URL
        header_img = soup.select_one("img.content-header-img")
        img_url = None
        if header_img:
            img_url = self._select_srcset_best(header_img.get("srcset", "")) or header_img.get("src")
        if not img_url:
            img_url = self._extract_meta(soup, "og:image")
        if img_url and img_url.startswith("//"):
            img_url = "https:" + img_url
        elif img_url and img_url.startswith("/"):
            img_url = "https://manulization.com" + img_url

        # 2) title/name
        name_tag = soup.select_one("h1.content-header-h1 span.animal-name-text")
        name = self._collapse_whitespace(name_tag.get_text()) if name_tag else ""
        if not name:
            title = self._extract_title(soup)
            name = re.split(r"\s[-–|]\s", title)[0].strip() if title else ""

        short_name_tag = soup.select_one(
            "figcaption span.uploaded-image-caption-animal-institution span.animal-name-text"
        )
        if short_name_tag and short_name_tag.get_text(strip=True):
            short_name = self._collapse_whitespace(short_name_tag.get_text())
        else:
            short_name = name.split()[0] if name else ""

        # 3) description (optional)
        desc_tag = soup.select_one("p.article-paragraph.body-large")
        desc = self._collapse_whitespace(desc_tag.get_text()) if desc_tag else ""
        if not desc:
            desc = self._extract_meta(soup, "og:description") or ""
        if not desc:
            meta_desc = soup.select_one('meta[name="description"]')
            if meta_desc and meta_desc.get("content"):
                desc = meta_desc["content"].strip()

        # 4) location
        location_tag = soup.select_one("p.content-header-subheader")
        location = self._collapse_whitespace(location_tag.get_text()) if location_tag else ""

        image = self._download_image(img_url) if img_url else None

        return ManulData(
            name=name,
            short_name=short_name,
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
