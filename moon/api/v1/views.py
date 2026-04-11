from django.shortcuts import get_object_or_404
from django.contrib.auth.models import User

from rest_framework.decorators import api_view, permission_classes, authentication_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from rest_framework_simplejwt.views import TokenObtainPairView

from datetime import datetime, time, UTC, timedelta

from yaml import serializer
from moon.engine.phase import find_previous_new_moon, find_next_new_moon, find_new_moon_on_date
from moon.models import Observation, FavouriteLocation
from moon.models import UserProfile, EmailVerificationToken, PasswordResetToken
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
     VerifyEmailSerializer,
     PasswordResetRequestSerializer,
     PasswordResetConfirmSerializer,
     ResendVerificationEmailSerializer,
    )

from django.core.mail import send_mail
from django.conf import settings
from django.db import transaction
import secrets


def _frontend_url(path: str) -> str:
    return f"{settings.FRONTEND_URL.rstrip('/')}/{path.lstrip('/')}"


def _select_active_new_moon_for_visibility(selected_dt_utc, threshold_days=5):
    """
    Use the most recent conjunction for up to `threshold_days` after it.
    After that threshold, switch to the next conjunction.
    """
    previous_new_moon_utc = find_previous_new_moon(selected_dt_utc + timedelta(seconds=1))
    next_new_moon_utc = find_next_new_moon(selected_dt_utc)

    days_since_previous = (selected_dt_utc - previous_new_moon_utc).total_seconds() / 86400.0
    if days_since_previous <= threshold_days:
        return previous_new_moon_utc
    return next_new_moon_utc


def _visibility_switch_threshold_days():
    try:
        return max(0, int(getattr(settings, "VISIBILITY_NEW_MOON_SWITCH_DAYS", 5)))
    except (TypeError, ValueError):
        return 5


class EmailVerifiedTokenObtainPairSerializer(TokenObtainPairSerializer):
    def validate(self, attrs):
        data = super().validate(attrs)
        if settings.DEBUG:
            return data
        profile = UserProfile.objects.filter(user=self.user).first()
        if not profile or not profile.email_verified:
            raise AuthenticationFailed("Email is not verified. Please verify your email before logging in.")
        return data


class EmailVerifiedTokenObtainPairView(TokenObtainPairView):
    serializer_class = EmailVerifiedTokenObtainPairSerializer


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

    # UX rule: only switch to the upcoming conjunction if we are > 5 days past
    # the most recent conjunction relative to the selected date.
    active_new_moon_utc = _select_active_new_moon_for_visibility(
        selected_dt_utc,
        threshold_days=_visibility_switch_threshold_days(),
    )

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

    # UX rule: only switch to the upcoming conjunction if we are > 5 days past
    # the most recent conjunction relative to the selected date.
    active_new_moon_utc = _select_active_new_moon_for_visibility(
        selected_dt_utc,
        threshold_days=_visibility_switch_threshold_days(),
    )

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
                "sunset_utc": n.sunset_utc,
                "moonset_utc": n.moonset_utc,
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

    email_send_failed = False
    with transaction.atomic():
        user = serializer.save()
        UserProfile.objects.get_or_create(user=user)
        try:
            _send_verification_email(user)
        except Exception:
            if not settings.DEBUG:
                raise
            email_send_failed = True

    if email_send_failed:
        detail_message = (
            "Account created, but verification email could not be sent in development mode. "
            "Please check SMTP settings before production."
        )
    else:
        detail_message = "Verification email sent. Please check your inbox."

    refresh = RefreshToken.for_user(user)

    return Response(
        {
            "user": {
                "id": user.id,
                "username": user.username,
                "email": user.email,
                "email_verified": False,
            },
            "refresh": str(refresh),
            "access": str(refresh.access_token),
            "detail": detail_message,
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


def _send_verification_email(user):
    """Generate and send email verification token."""
    token = secrets.token_urlsafe(32)
    EmailVerificationToken.objects.filter(user=user).delete()
    EmailVerificationToken.objects.create(user=user, token=token)

    verification_url = f"{_frontend_url('/verify-email/')}?token={token}"
    send_mail(
        subject="Verify your LunaVis email",
        message=f"Click the link to verify your email: {verification_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return token


def _send_password_reset_email(user):
    """Generate and send password reset token."""
    token = secrets.token_urlsafe(32)
    PasswordResetToken.objects.create(user=user, token=token)

    reset_url = f"{_frontend_url('/reset-password/')}?token={token}"
    send_mail(
        subject="Reset your LunaVis password",
        message=f"Click the link to reset your password: {reset_url}",
        from_email=settings.DEFAULT_FROM_EMAIL,
        recipient_list=[user.email],
        fail_silently=False,
    )
    return token


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def send_verification_email_view(request):
    """Send email verification link to current user."""
    user = request.user
    try:
        _send_verification_email(user)
        return Response(
            {"detail": f"Verification email sent to {user.email}"},
            status=status.HTTP_200_OK
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to send email: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([IsAuthenticated])
def test_email_view(request):
    """Send a test email to the currently authenticated user."""
    user = request.user
    recipient = user.email

    if not recipient:
        return Response(
            {"detail": "Current user does not have an email address."},
            status=status.HTTP_400_BAD_REQUEST,
        )

    if not settings.EMAIL_HOST_USER or not settings.EMAIL_HOST_PASSWORD:
        return Response(
            {
                "detail": (
                    "SMTP is not configured: set EMAIL_HOST_USER and EMAIL_HOST_PASSWORD "
                    "(for Gmail, use an App Password)."
                )
            },
            status=status.HTTP_400_BAD_REQUEST,
        )

    try:
        send_mail(
            subject="LunaVis SMTP Test",
            message=(
                "This is a test email from LunaVis.\n\n"
                f"Backend: {settings.EMAIL_BACKEND}\n"
                f"Host: {settings.EMAIL_HOST}:{settings.EMAIL_PORT}\n"
                f"TLS: {settings.EMAIL_USE_TLS} | SSL: {getattr(settings, 'EMAIL_USE_SSL', False)}\n"
            ),
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[recipient],
            fail_silently=False,
        )
        return Response(
            {"detail": f"Test email sent to {recipient}."},
            status=status.HTTP_200_OK,
        )
    except Exception as e:
        return Response(
            {"detail": f"SMTP test failed: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR,
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def verify_email_view(request):
    """Verify email using token."""
    serializer = VerifyEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]

    try:
        email_token = EmailVerificationToken.objects.get(token=token)
        user = email_token.user
        
        profile, _ = UserProfile.objects.get_or_create(user=user)
        profile.email_verified = True
        profile.save()
        
        email_token.delete()
        
        return Response(
            {
                "detail": "Email verified successfully. You can now log in.",
                "login_url": _frontend_url('/login/'),
            },
            status=status.HTTP_200_OK
        )
    except EmailVerificationToken.DoesNotExist:
        return Response(
            {"error": "Invalid or expired verification token"},
            status=status.HTTP_400_BAD_REQUEST
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def resend_verification_email_view(request):
    """Resend verification email."""
    serializer = ResendVerificationEmailSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]

    try:
        user = User.objects.get(email=email)
        _send_verification_email(user)
        return Response(
            {"detail": f"Verification email sent to {email}"},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User with that email not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to send email: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_request_view(request):
    """Request password reset token."""
    serializer = PasswordResetRequestSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    email = serializer.validated_data["email"]

    try:
        user = User.objects.get(email=email)
        _send_password_reset_email(user)
        return Response(
            {"detail": f"Password reset email sent to {email}"},
            status=status.HTTP_200_OK
        )
    except User.DoesNotExist:
        return Response(
            {"error": "User with that email not found"},
            status=status.HTTP_404_NOT_FOUND
        )
    except Exception as e:
        return Response(
            {"error": f"Failed to send email: {str(e)}"},
            status=status.HTTP_500_INTERNAL_SERVER_ERROR
        )


@api_view(["POST"])
@permission_classes([AllowAny])
def password_reset_confirm_view(request):
    """Confirm password reset with token."""
    serializer = PasswordResetConfirmSerializer(data=request.data)
    serializer.is_valid(raise_exception=True)
    token = serializer.validated_data["token"]
    new_password = serializer.validated_data["password"]

    try:
        reset_token = PasswordResetToken.objects.get(token=token)
        user = reset_token.user
        
        user.set_password(new_password)
        user.save()
        
        PasswordResetToken.objects.filter(user=user).delete()
        
        return Response(
            {"detail": "Password reset successfully"},
            status=status.HTTP_200_OK
        )
    except PasswordResetToken.DoesNotExist:
        return Response(
            {"error": "Invalid or expired reset token"},
            status=status.HTTP_400_BAD_REQUEST
        )
