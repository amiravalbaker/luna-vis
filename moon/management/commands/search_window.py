from datetime import date
from django.core.management.base import BaseCommand

from moon.engine.night_search import scan_visibility_window


class Command(BaseCommand):
    help = "Scan several evenings for crescent visibility"

    def add_arguments(self, parser):
        parser.add_argument("--date", type=str, help="Start date YYYY-MM-DD")
        parser.add_argument("--nights", type=int, default=5)

    def handle(self, *args, **options):
        lat = 50.1186
        lon = -5.5372
        elevation = 36

        if options["date"]:
            year, month, day = map(int, options["date"].split("-"))
            start_date = date(year, month, day)
        else:
            start_date = date.today()

        result = scan_visibility_window(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            start_date=start_date,
            tz_name="Europe/London",
            nights=options["nights"],
        )

        self.stdout.write("")
        self.stdout.write("Visibility window search")
        self.stdout.write("------------------------")

        for night in result.nights:
            self.stdout.write(
                f"{night.date_local}: "
                f"age={night.age_hours:.1f}h, "
                f"visible={night.visible_count}, "
                f"maybe={night.maybe_count}, "
                f"not_visible={night.not_visible_count}, "
                f"consensus={night.consensus_fraction:.2f}"
            )

        self.stdout.write("")
        self.stdout.write(f"Optimistic date: {result.optimistic_date}")
        self.stdout.write(f"Majority date: {result.majority_date}")
        self.stdout.write(f"Conservative date: {result.conservative_date}")