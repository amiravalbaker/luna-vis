from rest_framework import serializers

from moon.models import Observation, ObservationSnapshot, ObservationPrediction


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