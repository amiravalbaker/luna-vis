from datetime import date
from django.core.management.base import BaseCommand

from moon.engine.daily_lunar import compute_daily_lunar_summary


class Command(BaseCommand):
    help = "Test daily lunar summary"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Date YYYY-MM-DD")

    def handle(self, *args, **options):
        lat = 50.1186
        lon = -5.5372
        elevation = 36

        if options["date"]:
            year, month, day = map(int, options["date"].split("-"))
            test_date = date(year, month, day)
        else:
            test_date = date.today()

        summary = compute_daily_lunar_summary(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            local_day=test_date,
            tz_name="Europe/London",
        )

        self.stdout.write("")
        self.stdout.write("Daily lunar summary")
        self.stdout.write("-------------------")
        self.stdout.write(f"Date: {summary.date_local}")
        self.stdout.write(f"Evaluation time (UTC): {summary.eval_time_utc}")
        self.stdout.write(f"Sunrise (UTC): {summary.sunrise_utc}")
        self.stdout.write(f"Sunset (UTC): {summary.sunset_utc}")
        self.stdout.write(f"Moonrise (UTC): {summary.moonrise_utc}")
        self.stdout.write(f"Moonset (UTC): {summary.moonset_utc}")
        self.stdout.write(f"Sun altitude: {summary.sun_alt_deg:.2f}°")
        self.stdout.write(f"Sun azimuth: {summary.sun_az_deg:.2f}°")
        self.stdout.write(f"Moon altitude: {summary.moon_alt_deg:.2f}°")
        self.stdout.write(f"Moon azimuth: {summary.moon_az_deg:.2f}°")
        self.stdout.write(f"Moon distance: {summary.moon_distance_km:.0f} km")
        self.stdout.write(f"Moon age: {summary.moon_age_hours:.1f} hours")
        self.stdout.write(f"Phase: {summary.phase_name}")