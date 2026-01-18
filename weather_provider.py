#!/usr/bin/env python3
"""Weather provider for Istanbul using Open-Meteo."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Optional

import requests


@dataclass(frozen=True)
class WeatherSnapshot:
    temperature_c: Optional[float]
    weather_code: Optional[int]
    temp_max_c: Optional[float]
    temp_min_c: Optional[float]


WEATHER_CODE_LABELS = {
    0: "Clear",
    1: "Mainly clear",
    2: "Partly cloudy",
    3: "Overcast",
    45: "Fog",
    48: "Rime fog",
    51: "Drizzle",
    53: "Drizzle",
    55: "Drizzle",
    56: "Freezing drizzle",
    57: "Freezing drizzle",
    61: "Rain",
    63: "Rain",
    65: "Rain",
    66: "Freezing rain",
    67: "Freezing rain",
    71: "Snow",
    73: "Snow",
    75: "Snow",
    77: "Snow grains",
    80: "Rain showers",
    81: "Rain showers",
    82: "Rain showers",
    85: "Snow showers",
    86: "Snow showers",
    95: "Thunderstorm",
    96: "Thunderstorm",
    99: "Thunderstorm",
}


class WeatherProvider:
    """Fetch weather for a fixed location."""

    def __init__(self, config: dict):
        weather_config = config.get("weather", {})
        self.latitude = weather_config.get("latitude", 41.0082)
        self.longitude = weather_config.get("longitude", 28.9784)
        self.timezone = weather_config.get("timezone", "Europe/Istanbul")
        self.timeout = weather_config.get("timeout", 10)

    def fetch_weather(self) -> WeatherSnapshot:
        params = {
            "latitude": self.latitude,
            "longitude": self.longitude,
            "current": "temperature_2m,weather_code",
            "daily": "temperature_2m_max,temperature_2m_min",
            "timezone": self.timezone,
        }
        response = requests.get("https://api.open-meteo.com/v1/forecast", params=params, timeout=self.timeout)
        response.raise_for_status()
        payload = response.json()

        current = payload.get("current", {})
        daily = payload.get("daily", {})

        temperature = current.get("temperature_2m")
        weather_code = current.get("weather_code")

        max_values = daily.get("temperature_2m_max", [])
        min_values = daily.get("temperature_2m_min", [])

        temp_max = max_values[0] if max_values else None
        temp_min = min_values[0] if min_values else None

        return WeatherSnapshot(
            temperature_c=temperature,
            weather_code=weather_code,
            temp_max_c=temp_max,
            temp_min_c=temp_min,
        )

    @staticmethod
    def describe_code(code: Optional[int]) -> str:
        if code is None:
            return "Unknown"
        return WEATHER_CODE_LABELS.get(code, "Unknown")
