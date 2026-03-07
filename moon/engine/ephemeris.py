from __future__ import annotations

from datetime import date, datetime, timedelta, UTC
from typing import Optional, Tuple

from skyfield.api import Loader, wgs84
from skyfield import almanac

from .context import ObservationContext


_loader = Loader("./skyfield-data")
_ts = _loader.timescale()
_eph = _loader("de421.bsp")

EARTH = _eph["earth"]
SUN = _eph["sun"]
MOON = _eph["moon"]


def _to_utc_range_for_local_date(local_day: date) -> Tuple[datetime, datetime]:
    start_utc = datetime(local_day.year, local_day.month, local_day.day, 0, 0, 0, tzinfo=UTC)
    end_utc = start_utc + timedelta(days=1)
    return start_utc, end_utc


def _find_sunset_utc(lat: float, lon: float, local_day: date) -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.sunrise_sunset(_eph, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 0:  # sunset
            return t.utc_datetime().replace(tzinfo=UTC)
    return None


def _find_moonset_utc(lat: float, lon: float, local_day: date) -> Optional[datetime]:
    start_utc, end_utc = _to_utc_range_for_local_date(local_day)
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    topos = wgs84.latlon(latitude_degrees=lat, longitude_degrees=lon)
    f = almanac.risings_and_settings(_eph, MOON, topos)

    times, events = almanac.find_discrete(t0, t1, f)
    for t, e in zip(times, events):
        if int(e) == 0:  # moonset
            return t.utc_datetime().replace(tzinfo=UTC)
    return None


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
    moon_alt, moon_az, _ = moon_app.altaz()

    elongation_deg = sun_app.separation_from(moon_app).degrees

    return (
        sun_alt.degrees,
        sun_az.degrees,
        moon_alt.degrees,
        moon_az.degrees,
        elongation_deg,
    )


def compute_context_for_evening(*, lat, lon, elevation_m, local_day, tz_name):
    sunset_utc = _find_sunset_utc(lat, lon, local_day)
    if sunset_utc is None:
        raise ValueError("No sunset found for this location/date.")

    moonset_utc = _find_moonset_utc(lat, lon, local_day)

    sun_alt, sun_az, moon_alt, moon_az, elongation_deg = _alt_az_at(
        lat, lon, elevation_m, sunset_utc
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
        elongation_deg=elongation_deg,
        lag_minutes=lag_minutes,
        moon_age_hours=None,
        illumination=None,
    )