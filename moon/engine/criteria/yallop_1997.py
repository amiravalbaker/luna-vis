import math
from .base import CriterionResult, Verdict, Capability
from ..context import ObservationContext


class Yallop1997:
    id = "yallop_1997"
    name = "Yallop (1997)"

    def _approx_crescent_width_arcmin(self, ctx: ObservationContext) -> float:
        # First-pass approximation using constant 15' semidiameter.
        return 15.0 * (1.0 - math.cos(math.radians(ctx.arcl_deg)))


    def _q_value(self, ctx: ObservationContext) -> float:
        w = self._approx_crescent_width_arcmin(ctx)
        return (
            ctx.arcv_deg
            - (11.8371 - 6.3226 * w + 0.7319 * w**2 - 0.1018 * w**3)
        ) / 10.0



    def evaluate(self, ctx: ObservationContext) -> CriterionResult:
        w = self._approx_crescent_width_arcmin(ctx)
        q = self._q_value(ctx)

        if q > 0.216:
            verdict = Verdict.VISIBLE
            capability = Capability.NAKED_EYE
            band = "A"
            reason = "Easily visible to the unaided eye."
        elif q > -0.014:
            verdict = Verdict.VISIBLE
            capability = Capability.NAKED_EYE
            band = "B"
            reason = "Visible under perfect conditions."
        elif q > -0.160:
            verdict = Verdict.MAYBE
            capability = Capability.NAKED_EYE
            band = "C"
            reason = "May need optical aid to find crescent before naked-eye sighting."
        elif q > -0.232:
            verdict = Verdict.MAYBE
            capability = Capability.OPTICAL_AID
            band = "D"
            reason = "Will need optical aid to find crescent."
        elif q > -0.293:
            verdict = Verdict.NOT_VISIBLE
            capability = Capability.OPTICAL_AID
            band = "E"
            reason = "Below the normal limit for detection with a telescope."
        else:
            verdict = Verdict.NOT_VISIBLE
            capability = Capability.UNKNOWN
            band = "F"
            reason = "Not visible; below the Danjon-limit region."


        return CriterionResult(
            criterion_id=self.id,
            name=self.name,
            verdict=verdict,
            capability=capability,
            score=q,
            band=band,
            reason=reason,
            debug={
                "arcv_deg": ctx.arcv_deg,
                "arcl_deg": ctx.arcl_deg,
                "daz_deg": ctx.daz_deg,
                "approx_width_arcmin": w,
                "q": q,
            },
        )
    