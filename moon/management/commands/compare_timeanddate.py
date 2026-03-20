from datetime import UTC, datetime
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.management.base import BaseCommand, CommandError

from moon.engine.daily_lunar import compute_daily_lunar_summary


class Command(BaseCommand):
    help = "Print daily sun/moon values in local and UTC time for timeanddate.com comparison"

    def add_arguments(self, parser):
        parser.add_argument("--date", required=True, type=str, help="Date as YYYY-MM-DD")
        parser.add_argument("--lat", required=True, type=float, help="Latitude")
        parser.add_argument("--lon", required=True, type=float, help="Longitude")
        parser.add_argument("--tz", required=True, type=str, help="IANA timezone, e.g. Europe/London")
        parser.add_argument("--elevation", required=False, default=0, type=int, help="Elevation in meters")

    def _parse_date(self, value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError("--date must be in YYYY-MM-DD format") from exc

    def _fmt_dt(self, dt_value, tzinfo: ZoneInfo):
        if dt_value is None:
            return "N/A"
        utc_text = dt_value.astimezone(UTC).strftime("%Y-%m-%d %H:%M:%S %Z")
        local_text = dt_value.astimezone(tzinfo).strftime("%Y-%m-%d %H:%M:%S %Z")
        return f"{local_text}   |   {utc_text}"

    def handle(self, *args, **options):
        local_day = self._parse_date(options["date"])
        lat = options["lat"]
        lon = options["lon"]
        elevation_m = options["elevation"]
        tz_name = options["tz"]

        try:
            tzinfo = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise CommandError(f"Unknown timezone: {tz_name}") from exc

        summary = compute_daily_lunar_summary(
            lat=lat,
            lon=lon,
            elevation_m=elevation_m,
            local_day=local_day,
            tz_name=tz_name,
        )

        self.stdout.write("")
        self.stdout.write("LunaVis Daily Comparison Snapshot")
        self.stdout.write("--------------------------------")
        self.stdout.write(f"Input date (local): {summary.date_local}")
        self.stdout.write(f"Latitude / Longitude: {lat}, {lon}")
        self.stdout.write(f"Timezone: {tz_name}")
        self.stdout.write(f"Elevation (m): {elevation_m}")

        self.stdout.write("")
        self.stdout.write("Times (local | UTC)")
        self.stdout.write(f"Sunrise: {self._fmt_dt(summary.sunrise_utc, tzinfo)}")
        self.stdout.write(f"Sunset:  {self._fmt_dt(summary.sunset_utc, tzinfo)}")
        self.stdout.write(f"Moonrise:{self._fmt_dt(summary.moonrise_utc, tzinfo)}")
        self.stdout.write(f"Moonset: {self._fmt_dt(summary.moonset_utc, tzinfo)}")

        self.stdout.write("")
        self.stdout.write("At evaluation time")
        self.stdout.write(f"Evaluation time: {self._fmt_dt(summary.eval_time_utc, tzinfo)}")
        self.stdout.write(f"Sun altitude: {summary.sun_alt_deg:.2f} deg")
        self.stdout.write(f"Sun azimuth: {summary.sun_az_deg:.2f} deg")
        self.stdout.write(f"Moon altitude: {summary.moon_alt_deg:.2f} deg")
        self.stdout.write(f"Moon azimuth: {summary.moon_az_deg:.2f} deg")
        self.stdout.write(f"Moon distance: {summary.moon_distance_km:.0f} km")
        self.stdout.write(f"Moon age: {summary.moon_age_hours:.2f} hours")
        self.stdout.write(f"Phase: {summary.phase_name}")
