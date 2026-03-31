from dataclasses import dataclass
from datetime import date, datetime, timedelta
from typing import List, Optional

from .criteria import CRITERIA
from .criteria.base import CriterionResult
from .aggregator import aggregate_results
from .ephemeris import compute_best_time_context
from .phase import moon_age_hours


@dataclass(frozen=True)
class NightResult:
    date_local: date
    sunset_utc: datetime
    moonset_utc: Optional[datetime]
    age_hours: float
    results: List[CriterionResult]
    visible_count: int
    maybe_count: int
    not_visible_count: int
    consensus_fraction: float


@dataclass(frozen=True)
class SearchResult:
    nights: List[NightResult]
    optimistic_date: Optional[date]
    majority_date: Optional[date]
    conservative_date: Optional[date]


def scan_visibility_window(*, lat, lon, elevation_m, start_date, tz_name, nights: int = 5):
    night_results: List[NightResult] = []

    optimistic_date = None
    majority_date = None
    conservative_date = None

    for i in range(nights):
        test_date = start_date + timedelta(days=i)

        ctx = compute_best_time_context(
            lat=lat,
            lon=lon,
            elevation_m=elevation_m,
            local_day=test_date,
            tz_name=tz_name,
        )

        age_hours = moon_age_hours(ctx.sunset_utc)

        # Always compute criterion outputs so UI can show band/score consistently,
        # including conjunction-day rows where moon age can be slightly negative.
        results = [criterion.evaluate(ctx) for criterion in CRITERIA]
        agg = aggregate_results(results)
        visible_count = agg.visible_count
        maybe_count = agg.maybe_count
        not_visible_count = agg.not_visible_count
        consensus_fraction = agg.consensus_fraction

        # Keep milestone dates constrained to the standard visibility window.
        if 0 <= age_hours <= 120:
            if optimistic_date is None and visible_count >= 1:
                optimistic_date = test_date

            if majority_date is None and visible_count > (agg.total_count / 2):
                majority_date = test_date

            if conservative_date is None and visible_count == agg.total_count:
                conservative_date = test_date

        night_results.append(
            NightResult(
                date_local=test_date,
                sunset_utc=ctx.sunset_utc,
                moonset_utc=ctx.moonset_utc,
                age_hours=age_hours,
                results=results,
                visible_count=visible_count,
                maybe_count=maybe_count,
                not_visible_count=not_visible_count,
                consensus_fraction=consensus_fraction,
            )
        )

    return SearchResult(
        nights=night_results,
        optimistic_date=optimistic_date,
        majority_date=majority_date,
        conservative_date=conservative_date,
    )