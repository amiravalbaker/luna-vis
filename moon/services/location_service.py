from __future__ import annotations

from typing import Optional

import requests
from timezonefinder import TimezoneFinder
from datetime import datetime
from zoneinfo import ZoneInfo

tf = TimezoneFinder()


def get_timezone_from_coords(lat: float, lon: float) -> str:
    """
    Return the IANA timezone name for a latitude/longitude pair.
    Falls back to UTC if no timezone can be determined.
    """
    tz = tf.timezone_at(lat=lat, lng=lon)
    return tz or "UTC"


def timezone_label(tz_name: str) -> str:
    """
    Return a human-friendly timezone label like:
    Malaysia Time (UTC+8)
    British Time (UTC+0)
    """

    try:
        tz = ZoneInfo(tz_name)
        now = datetime.now(tz)

        offset = now.utcoffset()
        total_seconds = offset.total_seconds()
        hours = int(total_seconds // 3600)
        minutes = int((abs(total_seconds) % 3600) // 60)

        if minutes:
            offset_str = f"UTC{sign}{abs(hours)}:{minutes:02d}"
        else:
            offset_str = f"UTC{sign}{abs(hours)}"

        sign = "+" if hours >= 0 else "-"
        

        # Extract city name from timezone
        parts = tz_name.split("/")
        city = parts[-1].replace("_", " ")

        return f"{city} Time ({offset_str})"

    except Exception:
        return tz_name



def get_timezone_metadata(lat: float, lon: float) -> dict:
    """
    Return both the IANA timezone and a user-friendly label.
    """
    tz = get_timezone_from_coords(lat, lon)
    return {
        "tz": tz,
        "tz_label": timezone_label(tz),
    }


def get_elevation_from_coords(lat: float, lon: float) -> float:
    """
    Look up elevation in metres from coordinates.

    Returns 0.0 if the elevation service fails or returns invalid data.
    """
    try:
        response = requests.get(
            "https://api.open-elevation.com/api/v1/lookup",
            params={"locations": f"{lat},{lon}"},
            timeout=5,
        )
        response.raise_for_status()

        data = response.json()
        results = data.get("results", [])

        if not results:
            return 0.0

        elevation = results[0].get("elevation")
        if elevation is None:
            return 0.0

        return float(elevation)

    except (requests.RequestException, ValueError, TypeError, KeyError):
        return 0.0


def get_location_metadata(lat: float, lon: float) -> dict:
    """
    Return all derived location metadata in one place.
    """
    tz_meta = get_timezone_metadata(lat, lon)
    elevation_m = get_elevation_from_coords(lat, lon)

    return {
        "tz": tz_meta["tz"],
        "tz_label": tz_meta["tz_label"],
        "elevation_m": round(elevation_m),
    }