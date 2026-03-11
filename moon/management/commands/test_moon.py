from django.core.management.base import BaseCommand
from datetime import date
from moon.engine.ephemeris import compute_context_for_evening, compute_best_time_context
from moon.engine.criteria import CRITERIA
from moon.engine.aggregator import aggregate_results


class Command(BaseCommand):
    help = "Test moon visibility engine"

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

        ctx = compute_context_for_evening(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            local_day=test_date,
            tz_name="Penzance",
        )

        best_ctx = compute_best_time_context(
            lat=lat,
            lon=lon,
            elevation_m=elevation,
            local_day=test_date,
            tz_name="Penzance",
        )

        self.stdout.write("")
        self.stdout.write("Best-time criteria results:")
        self.stdout.write("---------------------------")

        for criterion in CRITERIA:
            result = criterion.evaluate(best_ctx)
            self.stdout.write(f"{result.name}: {result.verdict}")
            self.stdout.write(f"  Band: {result.band}")
            self.stdout.write(f"  Reason: {result.reason}")
            if result.score is not None:
                self.stdout.write(f"  Score: {result.score:.2f}")
            self.stdout.write(f"  Debug: {result.debug}")
            self.stdout.write("")

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
        self.stdout.write(f"DAZ: {ctx.daz_deg:.2f}°")
        self.stdout.write(f"ARCV: {ctx.arcv_deg:.2f}°")
        self.stdout.write(f"ARCL: {ctx.arcl_deg:.2f}°")

        if ctx.lag_minutes is not None:
            self.stdout.write(f"Lag time: {ctx.lag_minutes} minutes")

        self.stdout.write("")
        self.stdout.write("Criteria results:")
        self.stdout.write("-----------------")

        
        results = []
        for criterion in CRITERIA:
            result = criterion.evaluate(ctx)
            results.append(result)

            self.stdout.write(f"{result.name}: {result.verdict}")
            self.stdout.write(f"  Band: {result.band}")
            self.stdout.write(f"  Reason: {result.reason}")
            if result.score is not None:
                self.stdout.write(f"  Score: {result.score:.2f}")
                self.stdout.write(f"  Debug: {result.debug}")
                self.stdout.write("")

        agg = aggregate_results(results)
        self.stdout.write("Summary:")
        self.stdout.write("--------")
        self.stdout.write(f"Visible: {agg.visible_count}")
        self.stdout.write(f"Maybe: {agg.maybe_count}")
        self.stdout.write(f"Not visible: {agg.not_visible_count}")
        self.stdout.write(f"Consensus fraction: {agg.consensus_fraction:.2f}")

        #self.stdout.write("")
        #self.stdout.write("Feature snapshot:")
        #self.stdout.write(str(ctx.features_dict()))