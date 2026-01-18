#!/usr/bin/env python3
"""
manul_scraper.py (STRICT + PI-SAFE)

Extract ONLY:
1) Header photo: main.page-main figure.content-header-figure img.content-header-img[src]
   - fallback ONLY if img.src missing: picture source[type="image/webp"][srcset] (pick largest)
   - skip placeholder SVG default-cover-img.svg
2) Name: h1.content-header-h1 span.animal-name-text
3) Short description: p.content-header-subheader (full text)

Important Raspberry Pi stability:
- DO NOT decode WebP with Pillow (can SIGILL on some Pi builds).
- Convert WebP -> PNG using ffmpeg (preferred) or dwebp (fallback),
  then open PNG with Pillow.

Deps:
  sudo apt-get install -y ffmpeg webp
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
        if isinstance(config_path_or_dict, (str, Path)):
            cfg_path = Path(config_path_or_dict)
            cfg = yaml.safe_load(cfg_path.read_text(encoding="utf-8")) or {}
        elif isinstance(config_path_or_dict, dict):
            cfg = config_path_or_dict
        else:
            raise TypeError(f"Expected config path or dict, got {type(config_path_or_dict)}")

        scraping = cfg.get("scraping", {}) if isinstance(cfg, dict) else {}
        manuls_scraping = scraping.get("manuls", {}) if isinstance(scraping, dict) else {}

        self.user_agent = manuls_scraping.get("user_agent", "manul/1.0 (+https://manulization.com)")
        self.timeout = int(manuls_scraping.get("timeout", 20))
        self.retry_attempts = int(manuls_scraping.get("retry_attempts", 3))
        self.retry_delay = float(manuls_scraping.get("retry_delay", 2))

        self.manul_urls = list(dict.fromkeys(MANUL_URLS))
        if not self.manul_urls:
            raise RuntimeError("MANUL_URLS is empty – nothing to scrape")

        self.session = requests.Session()
        self.session.headers.update(
            {
                "User-Agent": self.user_agent,
                "Accept": "image/avif,image/webp,image/apng,image/*,*/*;q=0.8",
                "Accept-Language": "en-US,en;q=0.9",
                "Connection": "keep-alive",
            }
        )

    def _get(self, url: str, extra_headers: Optional[dict] = None) -> Optional[requests.Response]:
        import time

        headers = dict(self.session.headers)
        if extra_headers:
            headers.update(extra_headers)

        for attempt in range(1, self.retry_attempts + 1):
            try:
                r = self.session.get(url, timeout=self.timeout, headers=headers)
                r.raise_for_status()
                return r
            except Exception as e:
                logger.warning(f"GET failed ({attempt}/{self.retry_attempts}) for {url}: {e}")
                if attempt < self.retry_attempts:
                    time.sleep(self.retry_delay)
        return None

    @staticmethod
    def _collapse_whitespace(text: str) -> str:
        return re.sub(r"\s+", " ", text or "").strip()

    @staticmethod
    def _select_srcset_best(srcset: str) -> Optional[str]:
        if not srcset:
            return None
        best_url = None
        best_w = -1.0
        for candidate in srcset.split(","):
            candidate = candidate.strip()
            if not candidate:
                continue
            parts = candidate.split()
            url = parts[0].strip()
            w = 0.0
            if len(parts) > 1:
                d = parts[1].strip()
                if d.endswith("w"):
                    try:
                        w = float(d[:-1])
                    except ValueError:
                        w = 0.0
                elif d.endswith("x"):
                    try:
                        w = float(d[:-1])
                    except ValueError:
                        w = 0.0
            if w > best_w:
                best_w = w
                best_url = url
        if best_url is None:
            first = srcset.split(",")[0].strip().split()
            return first[0].strip() if first else None
        return best_url

    @staticmethod
    def _looks_like_html(content: bytes, content_type: str) -> bool:
        ct = (content_type or "").lower()
        if ct.startswith("text/"):
            return True
        head = content[:2048].lower()
        return b"<!doctype html" in head or b"<html" in head

    @staticmethod
    def _is_webp_bytes(content: bytes, content_type: str, url: str) -> bool:
        ct_l = (content_type or "").lower()
        url_l = (url or "").lower()
        sig = len(content) >= 12 and content[:4] == b"RIFF" and content[8:12] == b"WEBP"
        return sig or ct_l.startswith("image/webp") or url_l.endswith(".webp")

    @staticmethod
    def _open_png_bytes(png_bytes: bytes) -> Optional[Image.Image]:
        try:
            im = Image.open(BytesIO(png_bytes))
            im.load()
            return im.convert("RGB")
        except Exception as e:
            logger.warning(f"Failed to open PNG bytes with Pillow: {e}")
            return None

    @staticmethod
    def _convert_webp_to_png_bytes_ffmpeg(webp_path: Path, png_path: Path) -> tuple[bool, str]:
        # -y overwrite, -loglevel error keeps output clean
        proc = subprocess.run(
            ["ffmpeg", "-hide_banner", "-loglevel", "error", "-y", "-i", str(webp_path), str(png_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            msg = ((proc.stderr or "") + " " + (proc.stdout or "")).strip()
            return False, msg
        return True, ""

    @staticmethod
    def _convert_webp_to_png_bytes_dwebp(webp_path: Path, png_path: Path) -> tuple[bool, str]:
        proc = subprocess.run(
            ["dwebp", str(webp_path), "-o", str(png_path)],
            capture_output=True,
            text=True,
            check=False,
        )
        if proc.returncode != 0:
            msg = ((proc.stderr or "") + " " + (proc.stdout or "")).strip()
            return False, msg
        return True, ""

    def _decode_image_bytes(self, img_url: str, content: bytes, content_type: str) -> Optional[Image.Image]:
        url_l = (img_url or "").lower()
        ct_l = (content_type or "").lower()

        # Block SVG placeholders
        if url_l.endswith(".svg") or ct_l.startswith("image/svg"):
            logger.warning(f"Blocked SVG image: {img_url}")
            return None

        # If HTML, skip
        if self._looks_like_html(content, content_type):
            logger.warning(
                f"Non-image response for {img_url} (Content-Type={content_type}). First bytes={content[:40]!r}"
            )
            return None

        is_webp = self._is_webp_bytes(content, content_type, img_url)

        # Non-WebP: Pillow is fine
        if not is_webp:
            try:
                im = Image.open(BytesIO(content))
                im.load()
                return im.convert("RGB")
            except Exception as e:
                logger.warning(f"Failed to decode non-WebP image {img_url}: {e}")
                return None

        # WebP: NEVER let Pillow touch it. Convert externally to PNG then open PNG.
        try:
            with tempfile.TemporaryDirectory() as td:
                td = Path(td)
                webp_path = td / "img.webp"
                png_path = td / "img.png"
                webp_path.write_bytes(content)

                ok, msg = self._convert_webp_to_png_bytes_ffmpeg(webp_path, png_path)
                if not ok:
                    # fallback to dwebp
                    ok2, msg2 = self._convert_webp_to_png_bytes_dwebp(webp_path, png_path)
                    if not ok2:
                        logger.warning(
                            f"WebP->PNG failed for {img_url}: ffmpeg_err={msg!r} dwebp_err={msg2!r}"
                        )
                        return None

                png_bytes = png_path.read_bytes()
                return self._open_png_bytes(png_bytes)
        except FileNotFoundError as e:
            logger.warning(f"Missing converter binary ({e}). Install: sudo apt-get install -y ffmpeg webp")
            return None
        except Exception as e:
            logger.warning(f"WebP decode exception for {img_url}: {e}")
            return None

    def _download_image(self, img_url: str, referer: Optional[str] = None) -> Optional[Image.Image]:
        extra_headers = {"Referer": referer} if referer else {}
        r = self._get(img_url, extra_headers=extra_headers)
        if r is None:
            return None
        content_type = r.headers.get("Content-Type", "") or ""
        return self._decode_image_bytes(img_url, r.content or b"", content_type)

    @staticmethod
    def _derive_short_name(full_name: str) -> str:
        s = (full_name or "").strip()
        if not s:
            return ""
        s = s.split(" the ", 1)[0].strip()
        s = s.split("(", 1)[0].strip()
        toks = s.split()
        return toks[0] if toks else s

    def get_random_manul(self) -> Optional[ManulData]:
        max_tries = min(25, len(self.manul_urls))
        tried = set()

        for _ in range(max_tries):
            url = random.choice(self.manul_urls)
            if url in tried:
                continue
            tried.add(url)

            logger.info(f"Selected manul URL: {url}")

            page = self._get(url)
            if page is None:
                logger.warning(f"Failed to fetch manul page, skipping: {url}")
                continue

            soup = BeautifulSoup(page.text, "html.parser")

            # 1) Header photo URL (STRICT)
            img_url = None
            img_tag = soup.select_one("main.page-main figure.content-header-figure img.content-header-img")
            if img_tag and img_tag.get("src"):
                img_url = img_tag["src"].strip()

            # Fallback ONLY if img src missing
            if not img_url:
                src_tag = soup.select_one(
                    "main.page-main figure.content-header-figure picture source[type='image/webp']"
                )
                if src_tag and src_tag.get("srcset"):
                    img_url = self._select_srcset_best(src_tag["srcset"])

            if not img_url:
                logger.warning(f"No header image found, skipping: {url}")
                continue

            # Normalize URL
            if img_url.startswith("//"):
                img_url = "https:" + img_url
            elif img_url.startswith("/"):
                img_url = "https://manulization.com" + img_url

            # Skip placeholder SVG pages
            img_url_l = img_url.lower()
            if img_url_l.endswith(".svg") or "default-cover-img.svg" in img_url_l:
                logger.warning(f"Placeholder header image (SVG), skipping: {img_url} from {url}")
                continue

            # 2) Name (STRICT)
            name_tag = soup.select_one("h1.content-header-h1 span.animal-name-text")
            if not name_tag:
                logger.warning(f"No name found, skipping: {url}")
                continue
            name = self._collapse_whitespace(name_tag.get_text())

            # 3) Subheader (STRICT)
            sub_tag = soup.select_one("p.content-header-subheader")
            if not sub_tag:
                logger.warning(f"No subheader found, skipping: {url}")
                continue
            subheader = self._collapse_whitespace(sub_tag.get_text(" ", strip=True))

            # Download + decode image (ONLY other fetch besides the page)
            image = self._download_image(img_url, referer=url)
            if image is None:
                logger.warning(f"Failed to decode image, skipping: {img_url} from {url}")
                continue

            short_name = self._derive_short_name(name)

            return ManulData(
                name=name,
                short_name=short_name,
                location="",
                description=subheader,
                image=image,
                source_url=url,
            )

        logger.error(f"Failed to find a valid manul with a photo after {max_tries} tries.")
        return None


if __name__ == "__main__":
    logging.basicConfig(level=logging.INFO)
    scraper = ManulScraper("config.yaml")
    m = scraper.get_random_manul()
    if m and m.image:
        print("OK:", m.name, "img=", m.image.size, "url=", m.source_url)
    else:
        print("Failed")
