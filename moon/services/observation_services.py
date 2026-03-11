from datetime import UTC

from moon.engine.ephemeris import compute_context_at_time
from moon.engine.phase import moon_age_hours
from moon.engine.criteria.yallop_1997 import Yallop1997
from moon.engine.criteria.odeh_2006 import Odeh2006
from moon.models import Observation, ObservationSnapshot, ObservationPrediction


def create_observation_with_analysis(
    *,
    user,
    observer_name: str,
    latitude: float,
    longitude: float,
    elevation_m: int,
    sky_condition: str,
    observation_time,
    time_spent_searching_minutes: int,
    visible: bool,
    detection_method: str,
    notes: str = "",
    tz_name: str = "UTC",
):
    if observation_time.tzinfo is None:
        observation_time = observation_time.replace(tzinfo=UTC)

    local_day = observation_time.date()

    observation = Observation.objects.create(
        user=user,
        observer_name=observer_name,
        latitude=latitude,
        longitude=longitude,
        elevation_m=elevation_m,
        sky_condition=sky_condition,
        observation_time=observation_time,
        time_spent_searching_minutes=time_spent_searching_minutes,
        visible=visible,
        detection_method=detection_method,
        notes=notes,
    )

    ctx = compute_context_at_time(
        lat=latitude,
        lon=longitude,
        elevation_m=elevation_m,
        local_day=local_day,
        tz_name=tz_name,
        when_utc=observation_time,
    )

    age_hours = moon_age_hours(observation_time)

    ObservationSnapshot.objects.create(
        observation=observation,
        sun_alt_deg=ctx.sun_alt_deg,
        sun_az_deg=ctx.sun_az_deg,
        moon_alt_deg=ctx.moon_alt_deg,
        moon_az_deg=ctx.moon_az_deg,
        moon_distance_km=ctx.moon_distance_km,
        elongation_deg=ctx.elongation_deg,
        daz_deg=ctx.daz_deg,
        arcv_deg=ctx.arcv_deg,
        arcl_deg=ctx.arcl_deg,
        lag_minutes=ctx.lag_minutes,
        moon_age_hours=age_hours,
        illumination_fraction=ctx.illumination,
    )

    criteria = [
        Yallop1997(),
        Odeh2006(),
    ]

    for criterion in criteria:
        result = criterion.evaluate(ctx)
        ObservationPrediction.objects.create(
            observation=observation,
            model_name=result.criterion_id,
            verdict=result.verdict.value,
            band=result.band or "",
            score=result.score,
        )

    return observation