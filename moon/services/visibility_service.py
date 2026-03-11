from moon.engine.night_search import scan_visibility_window
from moon.engine.ephemeris import compute_context_for_evening
from moon.engine.criteria import CRITERIA
from moon.engine.aggregator import aggregate_results
from moon.engine.phase import moon_age_hours


def get_visibility_for_date(*, lat, lon, elevation_m, local_day, tz_name):
    ctx = compute_context_for_evening(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
    )

    age_hours = moon_age_hours(ctx.sunset_utc)
    within_visibility_window = 0 <= age_hours <= 120

    if not within_visibility_window:
        results = []
        agg = None
    else:
        results = [criterion.evaluate(ctx) for criterion in CRITERIA]
        agg = aggregate_results(results)

    return {
        "date_local": local_day,
        "sunset_utc": ctx.sunset_utc,
        "moonset_utc": ctx.moonset_utc,
        "moon_age_hours": age_hours,
        "within_visibility_window": within_visibility_window,
        "criteria_results": results,
        "aggregate": agg,
    }


def get_visibility_window(*, lat, lon, elevation_m, start_date, tz_name, nights=5):
    return scan_visibility_window(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        start_date=start_date,
        tz_name=tz_name,
        nights=nights,
    )