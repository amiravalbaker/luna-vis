from rest_framework import serializers
from moon.models import FavouriteLocation

from moon.models import Observation, ObservationSnapshot, ObservationPrediction

from django.contrib.auth.models import User
from django.contrib.auth.password_validation import validate_password



class DailyQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    date = serializers.DateField()
    tz = serializers.CharField()
    elevation_m = serializers.IntegerField(required=False, default=0)


class VisibilityQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    date = serializers.DateField()
    tz = serializers.CharField()
    elevation_m = serializers.IntegerField(required=False, default=0)


class VisibilityWindowQuerySerializer(serializers.Serializer):
    lat = serializers.FloatField(min_value=-90, max_value=90)
    lon = serializers.FloatField(min_value=-180, max_value=180)
    start_date = serializers.DateField()
    tz = serializers.CharField()
    elevation_m = serializers.IntegerField(required=False, default=0)
    nights = serializers.IntegerField(required=False, default=5, min_value=1, max_value=10)


class ObservationSnapshotSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationSnapshot
        fields = [
            "sun_alt_deg",
            "sun_az_deg",
            "moon_alt_deg",
            "moon_az_deg",
            "moon_distance_km",
            "elongation_deg",
            "daz_deg",
            "arcv_deg",
            "arcl_deg",
            "lag_minutes",
            "moon_age_hours",
            "illumination_fraction",
            "created_at",
        ]


class ObservationPredictionSerializer(serializers.ModelSerializer):
    class Meta:
        model = ObservationPrediction
        fields = [
            "model_name",
            "verdict",
            "band",
            "score",
            "created_at",
        ]


class ObservationSerializer(serializers.ModelSerializer):
    snapshot = ObservationSnapshotSerializer(read_only=True)
    predictions = ObservationPredictionSerializer(many=True, read_only=True)

    class Meta:
        model = Observation
        fields = [
            "id",
            "user",
            "observer_name",
            "latitude",
            "longitude",
            "elevation_m",
            "sky_condition",
            "observation_time",
            "time_spent_searching_minutes",
            "visible",
            "detection_method",
            "notes",
            "created_at",
            "snapshot",
            "predictions",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
            "snapshot",
            "predictions",
        ]


class FavouriteLocationSerializer(serializers.ModelSerializer):
    class Meta:
        model = FavouriteLocation
        fields = [
            "id",
            "user",
            "name",
            "latitude",
            "longitude",
            "elevation_m",
            "created_at",
        ]
        read_only_fields = [
            "id",
            "user",
            "created_at",
        ]        

class RegisterSerializer(serializers.ModelSerializer):
    password = serializers.CharField(write_only=True, required=True)
    password_confirm = serializers.CharField(write_only=True, required=True)
    email = serializers.EmailField(required=True)

    class Meta:
        model = User
        fields = [
            "username",
            "email",
            "password",
            "password_confirm",
        ]

    def validate_username(self, value):
        if User.objects.filter(username=value).exists():
            raise serializers.ValidationError("A user with that username already exists.")
        return value

    def validate_email(self, value):
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with that email already exists.")
        return value

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError({"password_confirm": "Passwords do not match."})

        validate_password(attrs["password"])
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")

        user = User.objects.create_user(
            username=validated_data["username"],
            email=validated_data["email"],
            password=validated_data["password"],
        )
        return user
    

class MeSerializer(serializers.ModelSerializer):
    class Meta:
        model = User
        fields = [
            "id",
            "username",
            "email",
        ]