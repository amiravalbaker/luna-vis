from __future__ import annotations

import math

from datetime import date, datetime, timedelta, UTC
from typing import Optional, Tuple
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from skyfield.api import Loader, wgs84
from skyfield import almanac

from .context import ObservationContext


_loader = Loader("./skyfield-data")
_ts = _loader.timescale()
_eph = _loader("de421.bsp")

EARTH = _eph["earth"]
SUN = _eph["sun"]
MOON = _eph["moon"]


def _get_tzinfo(tz_name: str):
    try:
        return ZoneInfo(tz_name)
    except ZoneInfoNotFoundError:
        return UTC


def _to_utc_range_for_local_date(local_day: date, tz_name: str) -> Tuple[datetime, datetime]:
    tzinfo = _get_tzinfo(tz_name)
    start_local = datetime(local_day.year, local_day.month, local_day.day, 0, 0, 0, tzinfo=tzinfo)
    end_local = start_local + timedelta(days=1)
    return start_local.astimezone(UTC), end_local.astimezone(UTC)


def _find_sunrise_utc(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day, tz_name)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.sunrise_sunset(_eph, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 1:
            return t.utc_datetime().replace(tzinfo=UTC)
    return None


def _find_sunset_utc(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day, tz_name)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.sunrise_sunset(_eph, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 0:
            return t.utc_datetime().replace(tzinfo=UTC)
    return None


def _find_nearest_moonrise_utc(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> Optional[datetime]:
    # Fallback: if no moonrise occurs within this exact local date, use the nearest one
    # from neighboring dates so the daily view can still show a practical rise time.
    start_utc, _ = _to_utc_range_for_local_date(local_day - timedelta(days=1), tz_name)
    _, end_utc = _to_utc_range_for_local_date(local_day + timedelta(days=1), tz_name)

    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.risings_and_settings(_eph, MOON, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    moonrises = [t.utc_datetime().replace(tzinfo=UTC) for t, e in zip(times, events) if int(e) == 1]
    if not moonrises:
        return None

    local_start_utc, local_end_utc = _to_utc_range_for_local_date(local_day, tz_name)
    local_mid_utc = local_start_utc + ((local_end_utc - local_start_utc) / 2)

    return min(moonrises, key=lambda rise_utc: abs((rise_utc - local_mid_utc).total_seconds()))


def _find_moonrise_utc(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day, tz_name)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.risings_and_settings(_eph, MOON, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 1:
            return t.utc_datetime().replace(tzinfo=UTC)

    return _find_nearest_moonrise_utc(lat, lon, local_day, tz_name)


def _find_moonset_utc(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day, tz_name)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.risings_and_settings(_eph, MOON, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 0:
            return t.utc_datetime().replace(tzinfo=UTC)
    return None


def _find_daily_events(lat: float, lon: float, local_day: date, tz_name: str = "UTC") -> tuple[
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
    Optional[datetime],
]:
    sunrise_utc = _find_sunrise_utc(lat, lon, local_day, tz_name)
    sunset_utc = _find_sunset_utc(lat, lon, local_day, tz_name)
    moonrise_utc = _find_moonrise_utc(lat, lon, local_day, tz_name)
    moonset_utc = _find_moonset_utc(lat, lon, local_day, tz_name)
    return sunrise_utc, sunset_utc, moonrise_utc, moonset_utc


def _alt_az_at(
    lat: float,
    lon: float,
    elevation_m: Optional[int],
    when_utc: datetime,
):
    t = _ts.from_datetime(when_utc)

    observer = EARTH + wgs84.latlon(
        latitude_degrees=lat,
        longitude_degrees=lon,
        elevation_m=elevation_m or 0,
    )

    sun_app = observer.at(t).observe(SUN).apparent()
    moon_app = observer.at(t).observe(MOON).apparent()

    sun_alt, sun_az, _ = sun_app.altaz()
    moon_alt, moon_az, moon_distance = moon_app.altaz()

    elongation_deg = sun_app.separation_from(moon_app).degrees

    # Approximate phase angle using elongation
    phase_angle_deg =float(elongation_deg)

    # Illuminated fraction approximation
    illumination_fraction = (1.0 - math.cos(math.radians(phase_angle_deg))) / 2.0

    return (
        float(sun_alt.degrees),
        float(sun_az.degrees),
        float(moon_alt.degrees),
        float(moon_az.degrees),
        float(elongation_deg),
        float(moon_distance.km),
        float(phase_angle_deg),
        float(illumination_fraction),
    )


def _derive_visibility_geometry(
    sun_alt_deg: float,
    sun_az_deg: float,
    moon_alt_deg: float,
    moon_az_deg: float,
    elongation_deg: float,
):
    daz_deg = float(sun_az_deg - moon_az_deg)
    arcv_deg = float(moon_alt_deg - sun_alt_deg)
    arcl_deg = float(elongation_deg)
    return daz_deg, arcv_deg, arcl_deg


def _build_context_at_time(
    *,
    lat,
    lon,
    elevation_m,
    local_day,
    tz_name,
    when_utc: datetime,
    sunset_utc: datetime,
    moonset_utc: Optional[datetime],
):
    sun_alt, sun_az, moon_alt, moon_az, elongation_deg, moon_distance_km, phase_angle_deg, illumination_fraction = _alt_az_at(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        when_utc=when_utc,
    )

    daz_deg, arcv_deg, arcl_deg = _derive_visibility_geometry(
        sun_alt, sun_az, moon_alt, moon_az, elongation_deg
    )

    lag_minutes = None
    if moonset_utc is not None:
        lag_minutes = int(round((moonset_utc - sunset_utc).total_seconds() / 60.0))

    return ObservationContext(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        date_local=local_day,
        tz=tz_name,
        sunset_utc=sunset_utc,
        moonset_utc=moonset_utc,
        sun_alt_deg=sun_alt,
        sun_az_deg=sun_az,
        moon_alt_deg=moon_alt,
        moon_az_deg=moon_az,
        moon_distance_km=moon_distance_km,
        elongation_deg=elongation_deg,
        daz_deg=daz_deg,
        arcv_deg=arcv_deg,
        arcl_deg=arcl_deg,
        lag_minutes=lag_minutes,
        moon_age_hours=None,
        illumination=illumination_fraction,
    )


def compute_context_at_time(*, lat, lon, elevation_m, local_day, tz_name, when_utc: datetime):
    sunset_utc = _find_sunset_utc(lat, lon, local_day, tz_name)
    if sunset_utc is None:
        raise ValueError("No sunset found for this location/date.")

    moonset_utc = _find_moonset_utc(lat, lon, local_day, tz_name)

    return _build_context_at_time(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
        when_utc=when_utc,
        sunset_utc=sunset_utc,
        moonset_utc=moonset_utc,
    )


def compute_context_for_evening(*, lat, lon, elevation_m, local_day, tz_name):
    sunset_utc = _find_sunset_utc(lat, lon, local_day, tz_name)
    if sunset_utc is None:
        raise ValueError("No sunset found for this location/date.")

    moonset_utc = _find_moonset_utc(lat, lon, local_day, tz_name)

    return _build_context_at_time(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
        when_utc=sunset_utc,
        sunset_utc=sunset_utc,
        moonset_utc=moonset_utc,
    )


def compute_best_time_context(*, lat, lon, elevation_m, local_day, tz_name):
    sunset_utc = _find_sunset_utc(lat, lon, local_day, tz_name)
    if sunset_utc is None:
        raise ValueError("No sunset found for this location/date.")

    moonset_utc = _find_moonset_utc(lat, lon, local_day, tz_name)

    lag_minutes = 0
    if moonset_utc is not None:
        lag_minutes = int(round((moonset_utc - sunset_utc).total_seconds() / 60.0))

    best_time_utc = sunset_utc + timedelta(minutes=(4.0 / 9.0) * lag_minutes)

    return _build_context_at_time(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
        when_utc=best_time_utc,
        sunset_utc=sunset_utc,
        moonset_utc=moonset_utc,
    )