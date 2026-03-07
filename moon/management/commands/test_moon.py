from django.core.management.base import BaseCommand
from datetime import date

from moon.engine.ephemeris import compute_context_for_evening


class Command(BaseCommand):
    help = "Test moon visibility engine"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Date YYYY-MM-DD")

    def handle(self, *args, **options):

        lat = 51.5074
        lon = -0.1278
        elevation = 30

        if options["date"]:
            year, month, day = map(int, options["date"].split("-"))
            test_date = date(year, month, day)
        else:
            test_date = date.today()

        ctx = compute_context_for_evening(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            local_day=test_date,
            tz_name="Europe/London",
        )

        self.stdout.write("")
        self.stdout.write("Moon visibility engine test")
        self.stdout.write("----------------------------")

        self.stdout.write(f"Location: {lat}, {lon}")
        self.stdout.write(f"Date: {ctx.date_local}")

        self.stdout.write("")
        self.stdout.write(f"Sunset (UTC): {ctx.sunset_utc}")
        self.stdout.write(f"Moonset (UTC): {ctx.moonset_utc}")

        self.stdout.write("")
        self.stdout.write(f"Sun altitude: {ctx.sun_alt_deg:.2f}°")
        self.stdout.write(f"Moon altitude: {ctx.moon_alt_deg:.2f}°")

        self.stdout.write("")
        self.stdout.write(f"Elongation: {ctx.elongation_deg:.2f}°")

        if ctx.lag_minutes is not None:
            self.stdout.write(f"Lag time: {ctx.lag_minutes} minutes")

        self.stdout.write("")
        self.stdout.write("Feature snapshot:")
        self.stdout.write(str(ctx.features_dict()))