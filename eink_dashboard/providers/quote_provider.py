"""Daily quote provider."""

from __future__ import annotations

import json
from dataclasses import dataclass
from datetime import datetime
from pathlib import Path

from eink_dashboard.config import QuoteConfig


@dataclass(frozen=True)
class Quote:
    text: str
    author: str


class QuoteProvider:
    """Provides one deterministic quote per local day."""

    def __init__(self, config: QuoteConfig, project_root: Path):
        if config.source != "local_json":
            raise ValueError("Only local_json quote source is supported in this build")
        self.config = config
        self.project_root = project_root
        self.quotes = self._load_quotes()

    def get_daily_quote(self, now: datetime) -> Quote:
        if not self.quotes:
            return Quote(text="Build one useful thing before noon.", author="Dashboard")
        index = (now.date().toordinal() + self.config.daily_seed) % len(self.quotes)
        return self.quotes[index]

    def _load_quotes(self) -> list[Quote]:
        path = (self.project_root / self.config.quotes_file).resolve()
        payload = json.loads(path.read_text(encoding="utf-8"))
        quotes: list[Quote] = []
        for row in payload:
            text = str(row.get("text", "")).strip()
            author = str(row.get("author", "Unknown")).strip() or "Unknown"
            if text:
                quotes.append(Quote(text=text, author=author))
        return quotes
