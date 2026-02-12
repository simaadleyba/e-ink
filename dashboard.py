#!/usr/bin/env python3
"""CLI entrypoint for the Waveshare 7.5" e-ink dashboard."""

from __future__ import annotations

import argparse
import logging
import sys
from pathlib import Path

from eink_dashboard.app import DashboardApp


def parse_args() -> argparse.Namespace:
    parser = argparse.ArgumentParser(description="E-Ink Dashboard")
    parser.add_argument("--config", default="config.yaml", help="Path to YAML config")
    parser.add_argument(
        "--preview",
        action="store_true",
        help="Render PNG preview instead of writing to the e-ink panel",
    )
    parser.add_argument(
        "--output",
        default="preview/dashboard_preview.png",
        help="Preview image path used with --preview",
    )
    parser.add_argument("--verbose", action="store_true", help="Enable debug logging")
    return parser.parse_args()


def main() -> None:
    args = parse_args()
    logging.basicConfig(
        level=logging.DEBUG if args.verbose else logging.INFO,
        format="%(asctime)s - %(levelname)s - %(message)s",
    )

    try:
        app = DashboardApp(config_path=Path(args.config))
        success = app.run(preview=args.preview, preview_path=Path(args.output))
        app.cleanup()
        sys.exit(0 if success else 1)
    except KeyboardInterrupt:
        logging.info("Interrupted by user")
        sys.exit(130)
    except Exception as exc:
        logging.exception("Dashboard run failed: %s", exc)
        sys.exit(1)


if __name__ == "__main__":
    main()
