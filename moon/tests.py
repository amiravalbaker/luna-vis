from datetime import UTC, date, datetime
from types import SimpleNamespace
from unittest.mock import patch

from django.contrib.auth.models import User
from django.test import TestCase

from moon.engine.criteria.base import Verdict
from moon.engine.phase import moon_age_hours
from moon.services.observation_services import create_observation_with_analysis


def _parse_iso_utc(value: str) -> datetime:
	return datetime.fromisoformat(value.replace("Z", "+00:00"))


class ObservationTimezoneTests(TestCase):
	@patch("moon.services.observation_services.Odeh2006")
	@patch("moon.services.observation_services.Yallop1997")
	@patch("moon.services.observation_services.moon_age_hours", return_value=12.5)
	@patch("moon.services.observation_services.compute_context_at_time")
	def test_observation_uses_selected_timezone_for_local_day(
		self,
		mock_compute_context_at_time,
		_mock_moon_age_hours,
		mock_yallop_cls,
		mock_odeh_cls,
	):
		user = User.objects.create_user(username="tzuser", password="x", email="tz@example.com")

		mock_compute_context_at_time.return_value = SimpleNamespace(
			sun_alt_deg=1.0,
			sun_az_deg=2.0,
			moon_alt_deg=3.0,
			moon_az_deg=4.0,
			moon_distance_km=380000.0,
			elongation_deg=5.0,
			daz_deg=6.0,
			arcv_deg=7.0,
			arcl_deg=8.0,
			lag_minutes=40,
			illumination=0.1,
		)

		yallop_result = SimpleNamespace(
			criterion_id="yallop_1997",
			verdict=Verdict.VISIBLE,
			band="A",
			score=1.2,
		)
		odeh_result = SimpleNamespace(
			criterion_id="odeh_2006",
			verdict=Verdict.MAYBE,
			band="B",
			score=0.2,
		)

		mock_yallop_cls.return_value.evaluate.return_value = yallop_result
		mock_odeh_cls.return_value.evaluate.return_value = odeh_result

		naive_local = datetime(2026, 3, 20, 0, 30, 0)

		observation = create_observation_with_analysis(
			user=user,
			observer_name="Tester",
			latitude=24.7136,
			longitude=46.6753,
			elevation_m=600,
			sky_condition="CLEAR",
			observation_time=naive_local,
			time_spent_searching_minutes=15,
			visible=True,
			detection_method="NAKED_EYE",
			notes="",
			tz_name="Asia/Riyadh",
		)

		kwargs = mock_compute_context_at_time.call_args.kwargs
		self.assertEqual(kwargs["local_day"], date(2026, 3, 20))
		self.assertEqual(kwargs["when_utc"], datetime(2026, 3, 19, 21, 30, tzinfo=UTC))

		self.assertEqual(observation.predictions.count(), 2)
		self.assertIsNotNone(observation.snapshot)


class VisibilityMoonAgeTests(TestCase):
	def test_visibility_moon_age_matches_sunset_reference(self):
		response = self.client.get(
			"/api/v1/visibility/",
			{
				"lat": 50.1186,
				"lon": -5.5372,
				"date": "2026-03-20",
				"tz": "Europe/London",
				"elevation_m": 0,
			},
		)

		self.assertEqual(response.status_code, 200)
		payload = response.json()

		sunset_utc = _parse_iso_utc(payload["sunset_utc"])
		expected_age = moon_age_hours(sunset_utc)
		self.assertAlmostEqual(payload["moon_age_hours"], expected_age, places=6)
