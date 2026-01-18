#!/usr/bin/env python3
import time
import requests
from bs4 import BeautifulSoup
from manul_urls import MANUL_URLS

HEADERS = {"User-Agent": "manul/1.0 (+https://manulization.com)"}
TIMEOUT = 20

def has_real_photo(html: str) -> bool:
    soup = BeautifulSoup(html, "html.parser")
    img = soup.select_one("main.page-main figure.content-header-figure img.content-header-img")
    if not img or not img.get("src"):
        return False
    src = img["src"].strip().lower()
    if src.endswith(".svg") or "default-cover-img.svg" in src:
        return False
    return True

good, bad = [], []

for i, url in enumerate(MANUL_URLS, 1):
    try:
        r = requests.get(url, headers=HEADERS, timeout=TIMEOUT)
        r.raise_for_status()
        if has_real_photo(r.text):
            good.append(url)
        else:
            bad.append(url)
    except Exception:
        bad.append(url)
    time.sleep(0.3)  # be polite

print("GOOD =", len(good))
print("BAD  =", len(bad))
print("\n# Paste this back into manul_urls.py:\n")
print("MANUL_URLS = [")
for u in good:
    print(f'    "{u}",')
print("]")
print("\n# Removed (no photo / errors):")
for u in bad:
    print(u)
