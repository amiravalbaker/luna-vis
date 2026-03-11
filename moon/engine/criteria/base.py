from dataclasses import dataclass, field
from enum import Enum
from typing import Any


class Verdict(str, Enum):
    NOT_VISIBLE = "NOT_VISIBLE"
    MAYBE = "MAYBE"
    VISIBLE = "VISIBLE"


class Capability(str, Enum):
    NAKED_EYE = "NAKED_EYE"
    OPTICAL_AID = "OPTICAL_AID"
    IMAGING = "IMAGING"
    UNKNOWN = "UNKNOWN"


@dataclass(frozen=True)
class CriterionResult:
    criterion_id: str
    name: str
    verdict: Verdict
    capability: Capability = Capability.UNKNOWN
    score: float | None = None
    band: str | None = None
    reason: str = ""
    debug: dict[str, Any] = field(default_factory=dict)