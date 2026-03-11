from moon.engine.daily_lunar import compute_daily_lunar_summary


def get_daily_lunar_data(*, lat, lon, elevation_m, local_day, tz_name):
    return compute_daily_lunar_summary(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
    )