import csv
from datetime import datetime
from pathlib import Path

from django.core.management.base import BaseCommand, CommandError


class Command(BaseCommand):
    help = "Compare LunaVis CSV export against a reference CSV (e.g. timeanddate)"

    def add_arguments(self, parser):
        parser.add_argument("--ours", required=True, type=str, help="Path to LunaVis CSV")
        parser.add_argument("--theirs", required=True, type=str, help="Path to reference CSV")
        parser.add_argument("--tolerance-minutes", type=float, default=2.0, help="Allowed absolute difference in minutes")

        parser.add_argument("--ours-date-col", type=str, default="date_local")
        parser.add_argument("--ours-sunrise-col", type=str, default="sunrise_local")
        parser.add_argument("--ours-sunset-col", type=str, default="sunset_local")
        parser.add_argument("--ours-moonrise-col", type=str, default="moonrise_local")
        parser.add_argument("--ours-moonset-col", type=str, default="moonset_local")

        parser.add_argument("--theirs-date-col", type=str, default="date_local")
        parser.add_argument("--theirs-sunrise-col", type=str, default="sunrise_local")
        parser.add_argument("--theirs-sunset-col", type=str, default="sunset_local")
        parser.add_argument("--theirs-moonrise-col", type=str, default="moonrise_local")
        parser.add_argument("--theirs-moonset-col", type=str, default="moonset_local")

    def _load_csv(self, path: Path):
        if not path.exists():
            raise CommandError(f"CSV file not found: {path}")
        with path.open("r", encoding="utf-8", newline="") as f:
            return list(csv.DictReader(f))

    def _parse_date(self, text: str):
        value = (text or "").strip()
        if not value:
            return None

        for fmt in ("%Y-%m-%d", "%d/%m/%Y", "%m/%d/%Y", "%d %b %Y", "%d %B %Y"):
            try:
                return datetime.strptime(value, fmt).date()
            except ValueError:
                pass

        # Try ISO-like date-time forms by slicing first date part.
        if len(value) >= 10:
            try:
                return datetime.strptime(value[:10], "%Y-%m-%d").date()
            except ValueError:
                pass

        return None

    def _parse_time_on_date(self, date_value, text: str):
        raw = (text or "").strip()
        if not raw:
            return None

        # Common LunaVis format: YYYY-MM-DD HH:MM:SS TZ
        if len(raw) >= 19 and raw[4:5] == "-" and raw[7:8] == "-" and raw[10:11] == " ":
            try:
                return datetime.strptime(raw[:19], "%Y-%m-%d %H:%M:%S")
            except ValueError:
                pass

        # If only time is present, combine with date.
        if date_value is None:
            return None

        for fmt in ("%H:%M", "%H:%M:%S", "%I:%M %p", "%I:%M:%S %p"):
            try:
                t = datetime.strptime(raw, fmt).time()
                return datetime.combine(date_value, t)
            except ValueError:
                pass

        return None

    def _build_index(self, rows, date_col):
        index = {}
        for row in rows:
            date_obj = self._parse_date(row.get(date_col, ""))
            if date_obj is not None:
                index[date_obj.isoformat()] = row
        return index

    def _minutes_diff(self, ours_dt, theirs_dt):
        if ours_dt is None or theirs_dt is None:
            return None
        return (ours_dt - theirs_dt).total_seconds() / 60.0

    def handle(self, *args, **options):
        ours_path = Path(options["ours"])
        theirs_path = Path(options["theirs"])
        tolerance = float(options["tolerance_minutes"])

        ours_rows = self._load_csv(ours_path)
        theirs_rows = self._load_csv(theirs_path)

        ours_index = self._build_index(ours_rows, options["ours_date_col"])
        theirs_index = self._build_index(theirs_rows, options["theirs_date_col"])

        common_dates = sorted(set(ours_index.keys()) & set(theirs_index.keys()))
        if not common_dates:
            raise CommandError("No overlapping dates found between the two CSV files.")

        events = [
            ("sunrise", options["ours_sunrise_col"], options["theirs_sunrise_col"]),
            ("sunset", options["ours_sunset_col"], options["theirs_sunset_col"]),
            ("moonrise", options["ours_moonrise_col"], options["theirs_moonrise_col"]),
            ("moonset", options["ours_moonset_col"], options["theirs_moonset_col"]),
        ]

        mismatches = []
        checked_pairs = 0
        missing_pairs = 0

        for day in common_dates:
            ours_row = ours_index[day]
            theirs_row = theirs_index[day]
            date_obj = datetime.strptime(day, "%Y-%m-%d").date()

            for event_name, ours_col, theirs_col in events:
                ours_dt = self._parse_time_on_date(date_obj, ours_row.get(ours_col, ""))
                theirs_dt = self._parse_time_on_date(date_obj, theirs_row.get(theirs_col, ""))

                diff_min = self._minutes_diff(ours_dt, theirs_dt)
                if diff_min is None:
                    missing_pairs += 1
                    continue

                checked_pairs += 1
                abs_diff = abs(diff_min)
                if abs_diff > tolerance:
                    mismatches.append((day, event_name, diff_min, ours_row.get(ours_col, ""), theirs_row.get(theirs_col, "")))

        self.stdout.write("")
        self.stdout.write("CSV comparison summary")
        self.stdout.write("----------------------")
        self.stdout.write(f"Ours: {ours_path}")
        self.stdout.write(f"Theirs: {theirs_path}")
        self.stdout.write(f"Overlapping dates: {len(common_dates)}")
        self.stdout.write(f"Checked event pairs: {checked_pairs}")
        self.stdout.write(f"Missing/unparsed pairs: {missing_pairs}")
        self.stdout.write(f"Tolerance: {tolerance:.2f} minutes")
        self.stdout.write(f"Mismatches: {len(mismatches)}")

        if mismatches:
            self.stdout.write("")
            self.stdout.write("First mismatches (up to 25):")
            self.stdout.write("date,event,diff_minutes,ours,theirs")
            for day, event_name, diff_min, ours_val, theirs_val in mismatches[:25]:
                self.stdout.write(f"{day},{event_name},{diff_min:+.2f},{ours_val},{theirs_val}")
        else:
            self.stdout.write(self.style.SUCCESS("No mismatches above tolerance."))
