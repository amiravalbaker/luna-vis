import math

from .base import CriterionResult, Verdict, Capability
from ..context import ObservationContext


class Odeh2006:
    id = "odeh_2006"
    name = "Odeh (2006)"

    def _crescent_width_arcmin(self, ctx: ObservationContext) -> float:
        return ctx.topocentric_crescent_width_arcmin
    
    def _visibility_value(self, ctx: ObservationContext) -> float:
        w = self._crescent_width_arcmin(ctx)
        return ctx.arcv_deg - (
            -0.1018 * w**3 + 0.7319 * w**2 - 6.3226 * w + 7.1651
        )

    def evaluate(self, ctx: ObservationContext) -> CriterionResult:
        w = self._crescent_width_arcmin(ctx)
        v = self._visibility_value(ctx)

        if v >= 5.65:
            verdict = Verdict.VISIBLE
            capability = Capability.NAKED_EYE
            band = "A"
            reason = "Visible by naked eye."
        elif v >= 2.0:
            verdict = Verdict.MAYBE
            capability = Capability.NAKED_EYE
            band = "B"
            reason = "Visible by optical aid; may be seen by naked eye."
        elif v >= -0.96:
            verdict = Verdict.MAYBE
            capability = Capability.OPTICAL_AID
            band = "C"
            reason = "Visible by optical aid only."
        else:
            verdict = Verdict.NOT_VISIBLE
            capability = Capability.OPTICAL_AID
            band = "D"
            reason = "Not visible even by optical aid."

        return CriterionResult(
            criterion_id=self.id,
            name=self.name,
            verdict=verdict,
            capability=capability,
            score=v,
            band=band,
            reason=reason,
            debug={
                "arcv_deg": ctx.arcv_deg,
                "arcl_deg": ctx.arcl_deg,
                "topocentric_width_arcmin": w,
                "v": v,
            },
        )