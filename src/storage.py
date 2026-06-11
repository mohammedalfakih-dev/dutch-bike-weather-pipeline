"""Storage functions for Postgres and Blob Storage."""

import json
import logging
import os
from contextlib import closing
from datetime import datetime, timezone
from typing import Any

import pandas as pd
import psycopg2
from azure.core.exceptions import ResourceExistsError
from azure.storage.blob import BlobServiceClient

log = logging.getLogger(__name__)

TABLE_NAME = "bike_weather_forecasts"


def insert_readings(df: pd.DataFrame) -> None:
    """Insert a DataFrame of bike weather readings into Postgres.

    Creates the table in your personal schema from DB_SCHEMA.
    Example:
        schema = dev_mohammedalfakih_dev
        table = bike_weather_forecasts
        full table = dev_mohammedalfakih_dev.bike_weather_forecasts
    """
    db_url = os.environ["POSTGRES_URL"]
    schema = os.environ["DB_SCHEMA"]

    with closing(psycopg2.connect(db_url)) as conn:
        with conn.cursor() as cur:
            cur.execute(f"CREATE SCHEMA IF NOT EXISTS {schema}")  # noqa: S608
            cur.execute(f"SET search_path TO {schema}")  # noqa: S608

            cur.execute("""
                CREATE TABLE IF NOT EXISTS bike_weather_forecasts (
                    id SERIAL PRIMARY KEY,
                    city TEXT NOT NULL,
                    forecast_time TIMESTAMP NOT NULL,
                    temperature_2m DOUBLE PRECISION NOT NULL,
                    precipitation DOUBLE PRECISION NOT NULL,
                    wind_speed_10m DOUBLE PRECISION NOT NULL,
                    weather_code INTEGER NOT NULL,
                    bike_score INTEGER NOT NULL,
                    bike_advice TEXT NOT NULL,
                    ingested_at TIMESTAMPTZ NOT NULL DEFAULT NOW(),
                    UNIQUE (city, forecast_time)
                )
            """)

            for _, row in df.iterrows():
                cur.execute(
                    """
                    INSERT INTO bike_weather_forecasts (
                        city,
                        forecast_time,
                        temperature_2m,
                        precipitation,
                        wind_speed_10m,
                        weather_code,
                        bike_score,
                        bike_advice
                    )
                    VALUES (%s, %s, %s, %s, %s, %s, %s, %s)
                    ON CONFLICT (city, forecast_time)
                    DO UPDATE SET
                        temperature_2m = EXCLUDED.temperature_2m,
                        precipitation = EXCLUDED.precipitation,
                        wind_speed_10m = EXCLUDED.wind_speed_10m,
                        weather_code = EXCLUDED.weather_code,
                        bike_score = EXCLUDED.bike_score,
                        bike_advice = EXCLUDED.bike_advice,
                        ingested_at = NOW()
                    """,
                    (
                        row["city"],
                        row["forecast_time"],
                        row["temperature_2m"],
                        row["precipitation"],
                        row["wind_speed_10m"],
                        row["weather_code"],
                        row["bike_score"],
                        row["bike_advice"],
                    ),
                )

        conn.commit()

    log.info("Inserted or updated %d rows into %s.%s", len(df), schema, TABLE_NAME)


def upload_raw_json(raw_data: list[dict[str, Any]]) -> None:
    """Upload raw API response to Blob Storage as a JSON backup."""
    conn_str = os.environ["AZURE_STORAGE_CONNECTION_STRING"]
    client = BlobServiceClient.from_connection_string(conn_str)
    container = client.get_container_client("raw")

    try:
        container.create_container()
    except ResourceExistsError:
        pass

    blob_name = (
        f"bike-weather/{datetime.now(timezone.utc).strftime('%Y-%m-%d_%H%M%S')}.json"
    )

    container.upload_blob(
        name=blob_name,
        data=json.dumps(raw_data, default=str).encode("utf-8"),
        overwrite=True,
    )

    log.info("Uploaded raw data to blob: %s", blob_name)
