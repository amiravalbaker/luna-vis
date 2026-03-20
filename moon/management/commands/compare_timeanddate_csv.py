import csv
from datetime import UTC, datetime, timedelta
from pathlib import Path
from zoneinfo import ZoneInfo, ZoneInfoNotFoundError

from django.core.management.base import BaseCommand, CommandError

from moon.engine.daily_lunar import compute_daily_lunar_summary


class Command(BaseCommand):
    help = "Export daily comparison values to CSV for timeanddate.com side-by-side validation"

    def add_arguments(self, parser):
        parser.add_argument("--start-date", required=True, type=str, help="Start date as YYYY-MM-DD")
        parser.add_argument("--days", required=False, default=30, type=int, help="Number of days to export")
        parser.add_argument("--lat", required=True, type=float, help="Latitude")
        parser.add_argument("--lon", required=True, type=float, help="Longitude")
        parser.add_argument("--tz", required=True, type=str, help="IANA timezone, e.g. Europe/London")
        parser.add_argument("--elevation", required=False, default=0, type=int, help="Elevation in meters")
        parser.add_argument(
            "--output",
            required=False,
            type=str,
            help="Output CSV path (default: exports/timeanddate_compare_<start>_<days>d.csv)",
        )

    def _parse_date(self, value: str):
        try:
            return datetime.strptime(value, "%Y-%m-%d").date()
        except ValueError as exc:
            raise CommandError("--start-date must be in YYYY-MM-DD format") from exc

    def _iso_or_blank(self, dt_value):
        if dt_value is None:
            return ""
        return dt_value.astimezone(UTC).isoformat()

    def _local_text_or_blank(self, dt_value, tzinfo: ZoneInfo):
        if dt_value is None:
            return ""
        return dt_value.astimezone(tzinfo).strftime("%Y-%m-%d %H:%M:%S %Z")

    def handle(self, *args, **options):
        start_date = self._parse_date(options["start_date"])
        days = options["days"]
        lat = options["lat"]
        lon = options["lon"]
        elevation_m = options["elevation"]
        tz_name = options["tz"]

        if days < 1:
            raise CommandError("--days must be at least 1")

        try:
            tzinfo = ZoneInfo(tz_name)
        except ZoneInfoNotFoundError as exc:
            raise CommandError(f"Unknown timezone: {tz_name}") from exc

        if options.get("output"):
            output_path = Path(options["output"])
        else:
            output_dir = Path("exports")
            output_dir.mkdir(parents=True, exist_ok=True)
            output_path = output_dir / f"timeanddate_compare_{start_date.isoformat()}_{days}d.csv"

        rows = []

        for i in range(days):
            local_day = start_date + timedelta(days=i)

            summary = compute_daily_lunar_summary(
                lat=lat,
                lon=lon,
                elevation_m=elevation_m,
                local_day=local_day,
                tz_name=tz_name,
            )

            rows.append(
                {
                    "date_local": summary.date_local.isoformat(),
                    "timezone": tz_name,
                    "lat": lat,
                    "lon": lon,
                    "elevation_m": elevation_m,
                    "sunrise_local": self._local_text_or_blank(summary.sunrise_utc, tzinfo),
                    "sunrise_utc": self._iso_or_blank(summary.sunrise_utc),
                    "sunset_local": self._local_text_or_blank(summary.sunset_utc, tzinfo),
                    "sunset_utc": self._iso_or_blank(summary.sunset_utc),
                    "moonrise_local": self._local_text_or_blank(summary.moonrise_utc, tzinfo),
                    "moonrise_utc": self._iso_or_blank(summary.moonrise_utc),
                    "moonset_local": self._local_text_or_blank(summary.moonset_utc, tzinfo),
                    "moonset_utc": self._iso_or_blank(summary.moonset_utc),
                    "eval_time_local": self._local_text_or_blank(summary.eval_time_utc, tzinfo),
                    "eval_time_utc": self._iso_or_blank(summary.eval_time_utc),
                    "sun_alt_deg": f"{summary.sun_alt_deg:.6f}",
                    "sun_az_deg": f"{summary.sun_az_deg:.6f}",
                    "moon_alt_deg": f"{summary.moon_alt_deg:.6f}",
                    "moon_az_deg": f"{summary.moon_az_deg:.6f}",
                    "moon_distance_km": f"{summary.moon_distance_km:.3f}",
                    "moon_age_hours": f"{summary.moon_age_hours:.6f}",
                    "phase_name": summary.phase_name,
                    "illumination_fraction": "" if summary.illumination_fraction is None else f"{summary.illumination_fraction:.8f}",
                }
            )

        fieldnames = [
            "date_local",
            "timezone",
            "lat",
            "lon",
            "elevation_m",
            "sunrise_local",
            "sunrise_utc",
            "sunset_local",
            "sunset_utc",
            "moonrise_local",
            "moonrise_utc",
            "moonset_local",
            "moonset_utc",
            "eval_time_local",
            "eval_time_utc",
            "sun_alt_deg",
            "sun_az_deg",
            "moon_alt_deg",
            "moon_az_deg",
            "moon_distance_km",
            "moon_age_hours",
            "phase_name",
            "illumination_fraction",
        ]

        output_path.parent.mkdir(parents=True, exist_ok=True)
        with output_path.open("w", newline="", encoding="utf-8") as csvfile:
            writer = csv.DictWriter(csvfile, fieldnames=fieldnames)
            writer.writeheader()
            writer.writerows(rows)

        self.stdout.write("")
        self.stdout.write(self.style.SUCCESS("CSV export complete"))
        self.stdout.write(f"Rows: {len(rows)}")
        self.stdout.write(f"File: {output_path}")
