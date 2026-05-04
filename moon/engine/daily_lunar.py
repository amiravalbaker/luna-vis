from dataclasses import dataclass
from datetime import date, datetime, time, UTC
from typing import Optional

from .ephemeris import _find_daily_events, _alt_az_at
from .phase import (
    get_lunar_phase_context,
    find_previous_new_moon,
    find_next_new_moon,
    find_previous_full_moon,
    find_next_full_moon,
)


@dataclass(frozen=True)
class DailyLunarSummary:
    date_local: date
    tz: str
    eval_time_utc: datetime

    sunrise_utc: Optional[datetime]
    sunset_utc: Optional[datetime]
    moonrise_utc: Optional[datetime]
    moonset_utc: Optional[datetime]

    sun_alt_deg: float
    sun_az_deg: float
    moon_alt_deg: float
    moon_az_deg: float
    moon_distance_km: float

    moon_age_hours: float
    illumination_fraction: Optional[float]
    phase_name: str

    previous_new_moon_time_utc: Optional[datetime] = None
    next_new_moon_time_utc: Optional[datetime] = None
    previous_full_moon_time_utc: Optional[datetime] = None
    next_full_moon_time_utc: Optional[datetime] = None

    previous_phase_name: Optional[str] = None
    previous_phase_time_utc: Optional[datetime] = None
    next_phase_name: Optional[str] = None
    next_phase_time_utc: Optional[datetime] = None

def _default_eval_time_utc(local_day: date) -> datetime:
    now_utc = datetime.now(UTC)

    if local_day == now_utc.date():
        return now_utc

    return datetime.combine(local_day, time(12, 0), tzinfo=UTC)


def compute_daily_lunar_summary(*, lat, lon, elevation_m, local_day, tz_name):
    sunrise_utc, sunset_utc, moonrise_utc, moonset_utc = _find_daily_events(
        lat, lon, local_day, tz_name
    )

    eval_time_utc = _default_eval_time_utc(local_day)

    sun_alt_deg, sun_az_deg, moon_alt_deg, moon_az_deg, elongation_deg, moon_distance_km, phase_angle_deg, illumination_fraction, _topocentric_crescent_width_deg, _topocentric_crescent_width_arcmin = _alt_az_at(
        lat,
        lon,
        elevation_m,
        eval_time_utc,
    )

    phase_ctx = get_lunar_phase_context(eval_time_utc)
    age_hours = phase_ctx.moon_age_hours
    phase_name = phase_ctx.current_phase_name
    previous_new_moon_time_utc = find_previous_new_moon(eval_time_utc)
    next_new_moon_time_utc = find_next_new_moon(eval_time_utc)
    previous_full_moon_time_utc = find_previous_full_moon(eval_time_utc)
    next_full_moon_time_utc = find_next_full_moon(eval_time_utc)

    return DailyLunarSummary(
        date_local=local_day,
        tz=tz_name,
        eval_time_utc=eval_time_utc,
        sunrise_utc=sunrise_utc,
        sunset_utc=sunset_utc,
        moonrise_utc=moonrise_utc,
        moonset_utc=moonset_utc,
        sun_alt_deg=sun_alt_deg,
        sun_az_deg=sun_az_deg,
        moon_alt_deg=moon_alt_deg,
        moon_az_deg=moon_az_deg,
        moon_distance_km=moon_distance_km,
        moon_age_hours=age_hours,
        illumination_fraction=illumination_fraction,
        phase_name=phase_name,
        previous_new_moon_time_utc=previous_new_moon_time_utc,
        next_new_moon_time_utc=next_new_moon_time_utc,
        previous_full_moon_time_utc=previous_full_moon_time_utc,
        next_full_moon_time_utc=next_full_moon_time_utc,
        previous_phase_name=phase_ctx.previous_event.phase_name,
        previous_phase_time_utc=phase_ctx.previous_event.time_utc,
        next_phase_name=phase_ctx.next_event.phase_name,
        next_phase_time_utc=phase_ctx.next_event.time_utc,
    )