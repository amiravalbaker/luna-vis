from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime, timedelta, UTC, time, date as date_type

from skyfield.api import Loader
from skyfield import almanac


_loader = Loader("./skyfield-data")
_ts = _loader.timescale()
_eph = _loader("de421.bsp")


PHASE_NAMES = {
    0: "New Moon",
    1: "First Quarter",
    2: "Full Moon",
    3: "Last Quarter",
}


@dataclass(frozen=True)
class LunarPhaseEvent:
    phase_index: int
    phase_name: str
    time_utc: datetime


@dataclass(frozen=True)
class LunarPhaseContext:
    previous_event: LunarPhaseEvent
    next_event: LunarPhaseEvent
    current_phase_name: str
    moon_age_hours: float


def _find_phase_events_between(start_utc: datetime, end_utc: datetime) -> list[LunarPhaseEvent]:
    t0 = _ts.from_datetime(start_utc)
    t1 = _ts.from_datetime(end_utc)

    phase_func = almanac.moon_phases(_eph)
    times, phases = almanac.find_discrete(t0, t1, phase_func)

    events: list[LunarPhaseEvent] = []
    for t, phase in zip(times, phases):
        phase_index = int(phase)
        events.append(
            LunarPhaseEvent(
                phase_index=phase_index,
                phase_name=PHASE_NAMES[phase_index],
                time_utc=t.utc_datetime().replace(tzinfo=UTC),
            )
        )

    return events
def get_surrounding_phase_events(at_utc: datetime) -> tuple[LunarPhaseEvent, LunarPhaseEvent]:
    """
    Find the previous and next major lunar phase events around the given datetime.
    """
    start_utc = at_utc - timedelta(days=40)
    end_utc = at_utc + timedelta(days=40)

    events = _find_phase_events_between(start_utc, end_utc)
    if not events:
        raise ValueError("No lunar phase events found in search window.")

    previous_event = None
    next_event = None

    for event in events:
        if event.time_utc <= at_utc:
            previous_event = event
        elif event.time_utc > at_utc and next_event is None:
            next_event = event
            break

    if previous_event is None:
        raise ValueError("No previous lunar phase event found.")

    if next_event is None:
        raise ValueError("No next lunar phase event found.")

    return previous_event, next_event



def find_new_moon_on_date(day: date_type) -> datetime | None:
    start_utc = datetime.combine(day, time.min, tzinfo=UTC)
    end_utc = start_utc + timedelta(days=1)

    events = _find_phase_events_between(start_utc, end_utc)

    for event in events:
        if event.phase_index == 0:
            return event.time_utc

    return None


def find_previous_new_moon(before_utc: datetime) -> datetime:
    start_utc = before_utc - timedelta(days=35)
    events = _find_phase_events_between(start_utc, before_utc)

    previous_new_moon = None
    for event in events:
        if event.phase_index == 0:
            previous_new_moon = event.time_utc

    if previous_new_moon is None:
        raise ValueError("No previous new moon found in search interval.")

    return previous_new_moon

def find_next_new_moon(after_utc: datetime) -> datetime:
    end_utc = after_utc + timedelta(days=35)
    events = _find_phase_events_between(after_utc, end_utc)

    for event in events:
        if event.phase_index == 0 and event.time_utc > after_utc:
            return event.time_utc

    raise ValueError("No next new moon found in search interval.")

def moon_age_hours(at_utc: datetime) -> float:
    previous_new = find_previous_new_moon(at_utc)
    return (at_utc - previous_new).total_seconds() / 3600.0


def phase_name_from_datetime(at_utc: datetime) -> str:
    """
    Determine the descriptive moon phase from the surrounding exact phase events.
    """
    previous_event, next_event = get_surrounding_phase_events(at_utc)

    prev_idx = previous_event.phase_index
    next_idx = next_event.phase_index

    # Intervals:
    # New -> First Quarter = Waxing Crescent
    # First Quarter -> Full = Waxing Gibbous
    # Full -> Last Quarter = Waning Gibbous
    # Last Quarter -> New = Waning Crescent

    if prev_idx == 0 and next_idx == 1:
        # Very close to conjunction should still be shown as New Moon
        hours_since_prev = (at_utc - previous_event.time_utc).total_seconds() / 3600.0
        if hours_since_prev < 12:
            return "New Moon"
        return "Waxing Crescent"

    if prev_idx == 1 and next_idx == 2:
        return "Waxing Gibbous"

    if prev_idx == 2 and next_idx == 3:
        # Very close to full moon
        hours_since_prev = (at_utc - previous_event.time_utc).total_seconds() / 3600.0
        if hours_since_prev < 12:
            return "Full Moon"
        return "Waning Gibbous"

    if prev_idx == 3 and next_idx == 0:
        return "Waning Crescent"

    # Fallbacks at the exact quarter moments
    return previous_event.phase_name


def get_lunar_phase_context(at_utc: datetime) -> LunarPhaseContext:
    previous_event, next_event = get_surrounding_phase_events(at_utc)

    return LunarPhaseContext(
        previous_event=previous_event,
        next_event=next_event,
        current_phase_name=phase_name_from_datetime(at_utc),
        moon_age_hours=moon_age_hours(at_utc),
    )