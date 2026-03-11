from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework import status

from .serializers import (
    ObservationSerializer,
    DailyQuerySerializer,
    VisibilityQuerySerializer,
    VisibilityWindowQuerySerializer,
)

from moon.models import Observation
from moon.services.observation_services import create_observation_with_analysis
from moon.services.daily_service import get_daily_lunar_data
from moon.services.visibility_service import (
    get_visibility_for_date,
    get_visibility_window,
)


@api_view(["GET"])
def daily_view(request):
    serializer = DailyQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    summary = get_daily_lunar_data(
        lat=data["lat"],
        lon=data["lon"],
        elevation_m=data["elevation_m"],
        local_day=data["date"],
        tz_name=data["tz"],
    )

    return Response({
        "date_local": str(summary.date_local),
        "tz": summary.tz,
        "eval_time_utc": summary.eval_time_utc,
        "sunrise_utc": summary.sunrise_utc,
        "sunset_utc": summary.sunset_utc,
        "moonrise_utc": summary.moonrise_utc,
        "moonset_utc": summary.moonset_utc,
        "sun_alt_deg": summary.sun_alt_deg,
        "sun_az_deg": summary.sun_az_deg,
        "moon_alt_deg": summary.moon_alt_deg,
        "moon_az_deg": summary.moon_az_deg,
        "moon_distance_km": summary.moon_distance_km,
        "moon_age_hours": summary.moon_age_hours,
        "illumination_fraction": summary.illumination_fraction,
        "phase_name": summary.phase_name,
    })


@api_view(["GET"])
def visibility_view(request):
    serializer = VisibilityQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    result = get_visibility_for_date(
        lat=data["lat"],
        lon=data["lon"],
        elevation_m=data["elevation_m"],
        local_day=data["date"],
        tz_name=data["tz"],
    )

    criteria_payload = []
    for r in result["criteria_results"]:
        criteria_payload.append({
            "criterion_id": r.criterion_id,
            "name": r.name,
            "verdict": r.verdict,
            "capability": r.capability,
            "score": r.score,
            "band": r.band,
            "reason": r.reason,
        })

    agg = result["aggregate"]

    return Response({
        "date_local": str(result["date_local"]),
        "sunset_utc": result["sunset_utc"],
        "moonset_utc": result["moonset_utc"],
        "moon_age_hours": result["moon_age_hours"],
        "within_visibility_window": result["within_visibility_window"],
        "criteria": criteria_payload,
        "summary": None if agg is None else {
            "visible_count": agg.visible_count,
            "maybe_count": agg.maybe_count,
            "not_visible_count": agg.not_visible_count,
            "total_count": agg.total_count,
            "consensus_fraction": agg.consensus_fraction,
        }
    })


@api_view(["GET"])
def visibility_window_view(request):
    serializer = VisibilityWindowQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    result = get_visibility_window(
        lat=data["lat"],
        lon=data["lon"],
        elevation_m=data["elevation_m"],
        start_date=data["start_date"],
        tz_name=data["tz"],
        nights=data["nights"],
    )

    return Response({
        "start_date": str(data["start_date"]),
        "nights": data["nights"],
        "optimistic_date": result.optimistic_date,
        "majority_date": result.majority_date,
        "conservative_date": result.conservative_date,
        "results": [
            {
                "date_local": str(n.date_local),
                "age_hours": n.age_hours,
                "visible_count": n.visible_count,
                "maybe_count": n.maybe_count,
                "not_visible_count": n.not_visible_count,
                "consensus_fraction": n.consensus_fraction,
            }
            for n in result.nights
        ]
    })

@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def observations_view(request):
    if request.method == "GET":
        observations = Observation.objects.filter(user=request.user).order_by("-observation_time")
        serializer = ObservationSerializer(observations, many=True)
        return Response(serializer.data)

    serializer = ObservationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    observation = create_observation_with_analysis(
        user=request.user,
        observer_name=data.get("observer_name", ""),
        latitude=data["latitude"],
        longitude=data["longitude"],
        elevation_m=data.get("elevation_m", 0),
        sky_condition=data.get("sky_condition", Observation.SkyCondition.CLEAR),
        observation_time=data["observation_time"],
        time_spent_searching_minutes=data.get("time_spent_searching_minutes", 0),
        visible=data["visible"],
        detection_method=data.get("detection_method", Observation.DetectionMethod.NAKED_EYE),
        notes=data.get("notes", ""),
        tz_name=request.data.get("tz", "UTC"),
    )

    return Response(
        ObservationSerializer(observation).data,
        status=status.HTTP_201_CREATED,
    )