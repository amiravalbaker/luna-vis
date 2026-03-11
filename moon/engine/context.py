from dataclasses import dataclass
from datetime import date, datetime
from typing import Optional, Dict, Any


@dataclass(frozen=True)
class ObservationContext:
    lat: float
    lon: float
    elevation_m: Optional[int]

    date_local: date
    tz: str

    sunset_utc: datetime
    moonset_utc: Optional[datetime]

    sun_alt_deg: float
    sun_az_deg: float
    moon_alt_deg: float
    moon_az_deg: float
    moon_distance_km: float
    elongation_deg: float

    daz_deg: float
    arcv_deg: float
    arcl_deg: float

    lag_minutes: Optional[int]
    moon_age_hours: Optional[float] = None
    illumination: Optional[float] = None

    phase_angle_deg: Optional[float] = None
    illumination_fraction: Optional[float] = None


    def features_dict(self) -> Dict[str, Any]:
        return {
            "sun_alt_deg": self.sun_alt_deg,
            "sun_az_deg": self.sun_az_deg,
            "moon_alt_deg": self.moon_alt_deg,
            "moon_az_deg": self.moon_az_deg,
            "elongation_deg": self.elongation_deg,
            "daz_deg": self.daz_deg,
            "arcv_deg": self.arcv_deg,
            "arcl_deg": self.arcl_deg,
            "lag_minutes": self.lag_minutes,
            "moon_age_hours": self.moon_age_hours,
            "illumination": self.illumination,
            "phase_angle_deg": self.phase_angle_deg,
            "illumination_fraction": self.illumination_fraction,
            "moon_distance_km": self.moon_distance_km,
        }