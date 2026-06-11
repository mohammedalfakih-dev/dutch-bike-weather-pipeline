"""Pydantic models for validating Open-Meteo bike weather records."""

from datetime import datetime

from pydantic import BaseModel, Field, field_validator


class WeatherReading(BaseModel):
    """One weather forecast record before pandas transformations."""

    city: str = Field(min_length=1)
    forecast_time: datetime
    temperature_2m: float = Field(ge=-50, le=60)
    precipitation: float = Field(ge=0)
    wind_speed_10m: float = Field(ge=0, le=200)
    weather_code: int = Field(ge=0)

    @field_validator("forecast_time", mode="before")
    @classmethod
    def parse_forecast_time(cls, value: object) -> datetime:
        """Parse Open-Meteo ISO timestamp strings into datetime objects."""
        if isinstance(value, datetime):
            return value

        if isinstance(value, str):
            return datetime.fromisoformat(value)

        raise ValueError("forecast_time must be an ISO datetime string")
