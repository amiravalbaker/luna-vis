from datetime import datetime, timedelta, UTC


def estimate_previous_new_moon(before_utc: datetime) -> datetime:
    """
    Simple approximation for now.
    Replace later with a proper conjunction search.
    """
    synodic_month_days = 29.53058867
    reference_new_moon = datetime(2000, 1, 6, 18, 14, tzinfo=UTC)

    delta_days = (before_utc - reference_new_moon).total_seconds() / 86400.0
    cycles = int(delta_days // synodic_month_days)

    previous_new_moon = reference_new_moon + timedelta(days=cycles * synodic_month_days)
    while previous_new_moon > before_utc:
        previous_new_moon -= timedelta(days=synodic_month_days)

    return previous_new_moon


def moon_age_hours(at_utc: datetime) -> float:
    previous_new = estimate_previous_new_moon(at_utc)
    return (at_utc - previous_new).total_seconds() / 3600.0


def phase_name_from_age_hours(age_hours: float) -> str:
    age_days = age_hours / 24.0

    if age_days < 1.0:
        return "New Moon"
    if age_days < 6.4:
        return "Waxing Crescent"
    if age_days < 8.4:
        return "First Quarter"
    if age_days < 13.8:
        return "Waxing Gibbous"
    if age_days < 15.8:
        return "Full Moon"
    if age_days < 21.1:
        return "Waning Gibbous"
    if age_days < 23.1:
        return "Last Quarter"
    if age_days < 28.5:
        return "Waning Crescent"
    return "New Moon"