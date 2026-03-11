from django.db import models
from django.contrib.auth.models import User

# Create your models here.

class FavouriteLocation(models.Model):
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="favourite_locations")

    name = models.CharField(max_length=100)

    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation_m = models.IntegerField(default=0)

    created_at = models.DateTimeField(auto_now_add=True)

class Observation(models.Model):

    class DetectionMethod(models.TextChoices):
        NAKED_EYE = "NAKED_EYE", "Naked Eye"
        OPTICAL_AID = "OPTICAL_AID", "Optical Aid"
        BINOCULARS = "BINOCULARS", "Binoculars"
        TELESCOPE = "TELESCOPE", "Telescope"
        CAMERA = "CAMERA", "Camera / CCD"
        UNKNOWN = "UNKNOWN", "Unknown"

    class SkyCondition(models.TextChoices):
        CLEAR = "CLEAR", "Clear"
        PARTLY_CLOUDY = "PARTLY_CLOUDY", "Partly Cloudy"
        HAZY = "HAZY", "Hazy"
        CLOUDY = "CLOUDY", "Cloudy"

    user = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="observations"
    )
    observer_name = models.CharField(max_length=100, blank=True)
    
    latitude = models.FloatField()
    longitude = models.FloatField()
    elevation_m = models.IntegerField(default=0)
    sky_condition = models.CharField(
        max_length=20,
        choices=SkyCondition.choices,
        default=SkyCondition.CLEAR
    )

    observation_time = models.DateTimeField()
    time_spent_searching_minutes = models.IntegerField(default=0)
    visible = models.BooleanField()
    
    detection_method = models.CharField(
        max_length=20,
        choices=DetectionMethod.choices,
        default=DetectionMethod.NAKED_EYE
    )
    notes = models.TextField(blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        who = self.observer_name or (self.user.username if self.user else "Anonymous")
        return f"{who} - {self.observation_time} - visible={self.visible}"

class ObservationSnapshot(models.Model):

    observation = models.OneToOneField(
        Observation,
        on_delete=models.CASCADE,
        related_name="snapshot"
    )

    sun_alt_deg = models.FloatField(null=True, blank=True)
    sun_az_deg = models.FloatField(null=True, blank=True)

    moon_alt_deg = models.FloatField(null=True, blank=True)
    moon_az_deg = models.FloatField(null=True, blank=True)
    moon_distance_km = models.FloatField(null=True, blank=True)

    elongation_deg = models.FloatField(null=True, blank=True)
    daz_deg = models.FloatField(null=True, blank=True)
    arcv_deg = models.FloatField(null=True, blank=True)
    arcl_deg = models.FloatField(null=True, blank=True)

    lag_minutes = models.IntegerField(null=True, blank=True)
    moon_age_hours = models.FloatField(null=True, blank=True)
    illumination_fraction = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Snapshot for observation {self.observation_id}"

class ObservationPrediction(models.Model):

    observation = models.ForeignKey(
        Observation,
        on_delete=models.CASCADE,
        related_name="predictions"
    )

    model_name = models.CharField(max_length=50)
    verdict = models.CharField(max_length=20)
    band = models.CharField(max_length=10, blank=True)

    score = models.FloatField(null=True, blank=True)

    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.model_name} - {self.verdict} - {self.observation.observation_time}"