from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status

from datetime import datetime, time, UTC, timedelta

from yaml import serializer
from moon.engine.phase import find_previous_new_moon, find_next_new_moon, find_new_moon_on_date
from moon.models import Observation, FavouriteLocation
from moon.services.observation_services import create_observation_with_analysis
from moon.services.daily_service import get_daily_lunar_data
from moon.services.visibility_service import (get_visibility_for_date,get_visibility_window,  
    )

from moon.services.favourite_location_service import create_favourite_location

from moon.services.location_service import (
    get_timezone_from_coords,
    timezone_label,
    get_elevation_from_coords,
    get_location_metadata,
)

from .serializers import (
    DailyQuerySerializer,
    VisibilityQuerySerializer,
    VisibilityWindowQuerySerializer,
    ObservationSerializer,
    FavouriteLocationSerializer,
    RegisterSerializer,
    MeSerializer,
    LocationMetaQuerySerializer,
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
        "previous_phase_name": summary.previous_phase_name,
        "previous_phase_time_utc": summary.previous_phase_time_utc,
        "next_phase_name": summary.next_phase_name,
        "next_phase_time_utc": summary.next_phase_time_utc,
    })


@api_view(["GET"])
def visibility_view(request):
    serializer = VisibilityQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    selected_date = data["date"]
    lat = data["lat"]
    lon = data["lon"]
    elevation_m = data.get("elevation_m", 0)
    tz_name = data["tz"]

    selected_dt_utc = datetime.combine(selected_date, time(12, 0), tzinfo=UTC)

    # If selected date is itself a new moon date, use that lunation.
    same_day_new_moon_utc = find_new_moon_on_date(selected_date)
    active_new_moon_utc = same_day_new_moon_utc or find_next_new_moon(selected_dt_utc)

    visibility_anchor_date = active_new_moon_utc.date()

    previous_new_moon_utc = find_previous_new_moon(active_new_moon_utc - timedelta(seconds=1))
    next_new_moon_utc = find_next_new_moon(active_new_moon_utc + timedelta(seconds=1))

    result = get_visibility_for_date(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        local_day=visibility_anchor_date,
        tz_name=tz_name,
    )

    # Keep moon age tied to the active lunation anchor shown in the UI.
    anchor_moon_age_hours = (
        (result["sunset_utc"] - active_new_moon_utc).total_seconds() / 3600.0
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
        "selected_date": str(selected_date),
        "new_moon_date": str(visibility_anchor_date),
        "new_moon_conjunction_utc": active_new_moon_utc,
        "previous_new_moon_utc": previous_new_moon_utc,
        "next_new_moon_utc": next_new_moon_utc,
        "previous_new_moon_date": str(previous_new_moon_utc.date()),
        "next_new_moon_date": str(next_new_moon_utc.date()),

        "date_local": str(result["date_local"]),
        "sunset_utc": result["sunset_utc"],
        "moonset_utc": result["moonset_utc"],
        "moon_age_hours": anchor_moon_age_hours,
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

    selected_start_date = data["start_date"]
    lat = data["lat"]
    lon = data["lon"]
    elevation_m = data.get("elevation_m", 0)
    tz_name = data["tz"]
    nights = data.get("nights", 5)

    selected_dt_utc = datetime.combine(selected_start_date, time(12, 0), tzinfo=UTC)

    #If selected date is itself a new moon date, use that lunation.
    same_day_new_moon_utc = find_new_moon_on_date(selected_start_date)
    active_new_moon_utc = same_day_new_moon_utc or find_next_new_moon(selected_dt_utc)

    visibility_anchor_date = active_new_moon_utc.date()

    previous_new_moon_utc = find_previous_new_moon(active_new_moon_utc - timedelta(seconds=1))
    next_new_moon_utc = find_next_new_moon(active_new_moon_utc + timedelta(seconds=1))

    result = get_visibility_window(
        lat=lat,
        lon=lon,
        elevation_m=elevation_m,
        start_date=visibility_anchor_date,
        tz_name=tz_name,
        nights=nights,
    )

    # First instance of 100% consensus
    first_100_consensus_date = str(result.conservative_date) if result.conservative_date is not None else None


    return Response({
        "selected_date": str(selected_start_date),
        "new_moon_date": str(visibility_anchor_date),
        "new_moon_conjunction_utc": active_new_moon_utc,
        "previous_new_moon_utc": previous_new_moon_utc,
        "next_new_moon_utc": next_new_moon_utc,
        "previous_new_moon_date": str(previous_new_moon_utc.date()),
        "next_new_moon_date": str(next_new_moon_utc.date()),

        "start_date": str(visibility_anchor_date),
        "nights": nights,
        "optimistic_date": result.optimistic_date,
        "majority_date": result.majority_date,
        "conservative_date": result.conservative_date,
        "first_100_consensus_date": first_100_consensus_date,

        "results": [
            {
                "date_local": str(n.date_local),
                "age_hours": n.age_hours,
                "visible_count": n.visible_count,
                "maybe_count": n.maybe_count,
                "not_visible_count": n.not_visible_count,
                "consensus_fraction": n.consensus_fraction,
                "criteria": [
                    {
                        "criterion_id": r.criterion_id,
                        "name": r.name,
                        "verdict": r.verdict.value,
                        "reason": r.reason,
                        "band": r.band,
                        "score": r.score,
                    }
                    for r in n.results
                ],
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


@api_view(["GET", "POST"])
@permission_classes([IsAuthenticated])
def favourites_view(request):
    if request.method == "GET":
        favourites = FavouriteLocation.objects.filter(user=request.user).order_by("name")
        serializer = FavouriteLocationSerializer(favourites, many=True)
        return Response(serializer.data)

    serializer = FavouriteLocationSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    favourite = create_favourite_location(
        user=request.user,
        name=data["name"],
        latitude=data["latitude"],
        longitude=data["longitude"],
        elevation_m=data.get("elevation_m", 0),
    )

    return Response(FavouriteLocationSerializer(favourite).data, status=status.HTTP_201_CREATED)


@api_view(["DELETE"])
@permission_classes([IsAuthenticated])
def favourite_detail_view(request, pk):
    favourite = get_object_or_404(FavouriteLocation, pk=pk, user=request.user)
    favourite.delete()
    return Response(status=status.HTTP_204_NO_CONTENT)

@api_view(["POST"])
@authentication_classes([])
@permission_classes([AllowAny])
def register_view(request):
    serializer = RegisterSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)

    user = serializer.save()

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
        },
        status=status.HTTP_201_CREATED,
    )


@api_view(["GET"])
@permission_classes([IsAuthenticated])
def me_view(request):
    serializer = MeSerializer(request.user)
    return Response(serializer.data)


@api_view(["GET"])
@permission_classes([AllowAny])
def location_meta_view(request):
    serializer = LocationMetaQuerySerializer(data=request.GET)
    serializer.is_valid(raise_exception=True)
    data = serializer.validated_data

    meta = get_location_metadata(data["lat"], data["lon"])
    return Response(meta)
