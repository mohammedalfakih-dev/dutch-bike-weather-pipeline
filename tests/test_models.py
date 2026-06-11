"""Tests for the WeatherReading Pydantic model."""

import pytest
from pydantic import ValidationError

from src.models import WeatherReading


def valid_record() -> dict[str, object]:
    """Return one valid Open-Meteo weather record."""
    return {
        "city": "Amsterdam",
        "forecast_time": "2026-06-10T12:00",
        "temperature_2m": 18.5,
        "precipitation": 0.2,
        "wind_speed_10m": 12.0,
        "weather_code": 3,
    }


def test_weather_reading_accepts_valid_data() -> None:
    """A complete valid record should be accepted."""
    reading = WeatherReading.model_validate(valid_record())

    assert reading.city == "Amsterdam"
    assert reading.temperature_2m == 18.5


def test_weather_reading_rejects_negative_precipitation() -> None:
    """Precipitation cannot be negative."""
    data = valid_record()
    data["precipitation"] = -1.0

    with pytest.raises(ValidationError):
        WeatherReading.model_validate(data)


def test_weather_reading_rejects_empty_city() -> None:
    """City cannot be empty."""
    data = valid_record()
    data["city"] = ""

    with pytest.raises(ValidationError):
        WeatherReading.model_validate(data)


def test_weather_reading_rejects_invalid_timestamp() -> None:
    """Forecast time must be a valid ISO timestamp."""
    data = valid_record()
    data["forecast_time"] = "not-a-date"

    with pytest.raises(ValidationError):
        WeatherReading.model_validate(data)
