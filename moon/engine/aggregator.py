from dataclasses import dataclass
from typing import Iterable

from .criteria.base import CriterionResult, Verdict


@dataclass(frozen=True)
class AggregateResult:
    visible_count: int
    maybe_count: int
    not_visible_count: int
    total_count: int
    consensus_fraction: float


def aggregate_results(results: Iterable[CriterionResult]) -> AggregateResult:
    results = list(results)

    visible_count = sum(1 for r in results if r.verdict == Verdict.VISIBLE)
    maybe_count = sum(1 for r in results if r.verdict == Verdict.MAYBE)
    not_visible_count = sum(1 for r in results if r.verdict == Verdict.NOT_VISIBLE)
    total_count = len(results)

    consensus_fraction = visible_count / total_count if total_count else 0.0

    return AggregateResult(
        visible_count=visible_count,
        maybe_count=maybe_count,
        not_visible_count=not_visible_count,
        total_count=total_count,
        consensus_fraction=consensus_fraction,
    )