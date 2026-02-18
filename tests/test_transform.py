"""Tests for transformation helpers."""

from __future__ import annotations

from accuweather_cli.transform import (
    condition_from_icon,
    transform_current_conditions,
    transform_daily_forecast,
    transform_hourly_forecast,
)


def test_condition_from_icon_mapping() -> None:
    assert condition_from_icon(1) == "sunny"
    assert condition_from_icon(11) == "fog"
    assert condition_from_icon(999) is None


def test_transform_current_conditions() -> None:
    raw = {
        "WeatherIcon": 1,
        "WeatherText": "sunny",
        "Temperature": {"Metric": {"Value": 20.5}},
        "ApparentTemperature": {"Metric": {"Value": 21.0}},
        "Pressure": {"Metric": {"Value": 1017.0}},
        "DewPoint": {"Metric": {"Value": 10.0}},
        "RelativeHumidity": 60,
        "Wind": {"Speed": {"Metric": {"Value": 14.0}}, "Direction": {"Degrees": 200}},
        "WindGust": {"Speed": {"Metric": {"Value": 24.0}}},
        "Visibility": {"Metric": {"Value": 10.0}},
        "UVIndex": 5,
        "CloudCover": 12,
        "PrecipitationSummary": {"PastHour": {"Metric": {"Value": 0.4}}},
        "PrecipitationType": "rain",
    }

    transformed = transform_current_conditions(raw)

    assert transformed["condition"] == "sunny"
    assert transformed["temperature_c"] == 20.5
    assert transformed["wind_bearing_deg"] == 200
    assert transformed["precipitation_mm_last_hour"] == 0.4


def test_transform_daily_forecast() -> None:
    raw = [
        {
            "EpochDate": 1700000000,
            "IconDay": 12,
            "LongPhraseDay": "showers",
            "TemperatureMax": {"Value": 8.0},
            "TemperatureMin": {"Value": 2.0},
            "RealFeelTemperatureMax": {"Value": 7.0},
            "RelativeHumidityDay": {"Average": 70},
            "CloudCoverDay": 80,
            "TotalLiquidDay": {"Value": 4.0},
            "PrecipitationProbabilityDay": 60,
            "WindDay": {"Speed": {"Value": 16.0}, "Direction": {"Degrees": 180}},
            "WindGustDay": {"Speed": {"Value": 28.0}},
            "UVIndex": {"Value": 3},
        }
    ]

    transformed = transform_daily_forecast(raw)

    assert transformed[0]["condition"] == "rainy"
    assert transformed[0]["temperature_max_c"] == 8.0
    assert transformed[0]["wind_speed_kmh"] == 16.0


def test_transform_hourly_forecast() -> None:
    raw = [
        {
            "EpochDateTime": 1700003600,
            "WeatherIcon": 33,
            "Temperature": {"Value": 6.0},
            "RealFeelTemperature": {"Value": 4.0},
            "RelativeHumidity": 81,
            "CloudCover": 45,
            "TotalLiquid": {"Value": 0.1},
            "PrecipitationProbability": 20,
            "Wind": {"Speed": {"Value": 12.0}, "Direction": {"Degrees": 250}},
            "WindGust": {"Speed": {"Value": 20.0}},
            "UVIndex": 0,
        }
    ]

    transformed = transform_hourly_forecast(raw)

    assert transformed[0]["condition"] == "clear-night"
    assert transformed[0]["temperature_c"] == 6.0
    assert transformed[0]["wind_gust_kmh"] == 20.0
