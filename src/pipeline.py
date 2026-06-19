"""Main pipeline: fetch Open-Meteo data, validate, transform, and store."""

import logging
import os
import sys
from typing import Any

import pandas as pd
import requests
from dotenv import load_dotenv
from pydantic import ValidationError

from src.models import WeatherReading
from src.storage import insert_readings, upload_raw_json

load_dotenv()

logging.basicConfig(
    level=os.getenv("LOG_LEVEL", "INFO"),
    format="%(asctime)s %(levelname)s %(message)s",
)
logging.getLogger("azure").setLevel(logging.WARNING)
log = logging.getLogger(__name__)


OPEN_METEO_URL = "https://api.open-meteo.com/v1/forecast"


CITIES = {
    "Amsterdam": {"latitude": 52.37, "longitude": 4.89},
    "Rotterdam": {"latitude": 51.92, "longitude": 4.48},
    "Utrecht": {"latitude": 52.09, "longitude": 5.12},
    "Den Haag": {"latitude": 52.08, "longitude": 4.30},
    "Eindhoven": {"latitude": 51.44, "longitude": 5.48},
}


def fetch_city_forecast(
    city: str, latitude: float, longitude: float
) -> list[dict[str, Any]]:
    """Fetch one day of hourly weather forecasts for one city."""
    log.info("Fetching forecast for %s", city)

    params = {
        "latitude": latitude,
        "longitude": longitude,
        "hourly": "temperature_2m,precipitation,wind_speed_10m,weather_code",
        "forecast_days": 1,
        "timezone": "Europe/Amsterdam",
    }

    response = requests.get(OPEN_METEO_URL, params=params, timeout=30)
    response.raise_for_status()

    payload = response.json()
    hourly = payload["hourly"]

    records = []

    for index, forecast_time in enumerate(hourly["time"]):
        records.append(
            {
                "city": city,
                "forecast_time": forecast_time,
                "temperature_2m": hourly["temperature_2m"][index],
                "precipitation": hourly["precipitation"][index],
                "wind_speed_10m": hourly["wind_speed_10m"][index],
                "weather_code": hourly["weather_code"][index],
            }
        )

    log.info("Fetched %d records for %s", len(records), city)
    return records


def fetch_data() -> list[dict[str, Any]]:
    """Fetch weather data for all configured Dutch cities."""
    all_records = []

    for city, coordinates in CITIES.items():
        city_records = fetch_city_forecast(
            city=city,
            latitude=coordinates["latitude"],
            longitude=coordinates["longitude"],
        )
        all_records.extend(city_records)

    log.info("Fetched %d total records from Open-Meteo", len(all_records))
    return all_records


def validate(raw_records: list[dict[str, Any]]) -> list[WeatherReading]:
    """Validate raw API records using Pydantic models; log and skip invalid ones."""
    valid = []

    for record in raw_records:
        try:
            valid.append(WeatherReading.model_validate(record))
        except ValidationError as error:
            log.warning("Skipping invalid record: %s", error)

    log.info("Validated %d / %d records", len(valid), len(raw_records))
    return valid


def transform(readings: list[WeatherReading]) -> pd.DataFrame:
    """Convert validated records to a DataFrame and apply real transformations."""
    df = pd.DataFrame([reading.model_dump() for reading in readings])

    df["forecast_time"] = pd.to_datetime(df["forecast_time"])

    df = df.dropna(
        subset=[
            "city",
            "forecast_time",
            "temperature_2m",
            "precipitation",
            "wind_speed_10m",
            "weather_code",
        ]
    )

    df["bike_score"] = 100

    df.loc[df["precipitation"] > 1.0, "bike_score"] -= 30
    df.loc[df["wind_speed_10m"] > 30.0, "bike_score"] -= 20
    df.loc[df["temperature_2m"] < 5.0, "bike_score"] -= 15
    df.loc[df["temperature_2m"] > 28.0, "bike_score"] -= 10

    df["bike_score"] = df["bike_score"].clip(lower=0, upper=100)

    df["bike_advice"] = "Avoid cycling if possible"
    df.loc[df["bike_score"] >= 40, "bike_advice"] = "Risky: rain, wind, cold, or heat"
    df.loc[df["bike_score"] >= 60, "bike_advice"] = "Okay, bring a jacket"
    df.loc[df["bike_score"] >= 80, "bike_advice"] = "Great for cycling"

    df = df.sort_values(["city", "forecast_time"])

    log.info("Transformed %d rows", len(df))
    return df


def run() -> None:
    """Run the full pipeline: fetch -> validate -> transform -> store."""
    log.info("Pipeline starting")

    raw = fetch_data()
    readings = validate(raw)

    if not readings:
        log.error("No valid records to store")
        sys.exit(1)

    df = transform(readings)

    insert_readings(df)
    upload_raw_json(raw)

    log.info("Pipeline finished: %d records stored", len(df))


if __name__ == "__main__":
    for var in ["POSTGRES_URL", "AZURE_STORAGE_CONNECTION_STRING", "DB_SCHEMA"]:
        if var not in os.environ:
            log.error("Missing required environment variable: %s", var)
            sys.exit(1)

    run()
