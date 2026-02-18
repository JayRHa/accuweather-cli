"""Transform raw AccuWeather responses into normalized CLI payloads."""

from __future__ import annotations

from collections.abc import Mapping
from datetime import datetime, timezone
from typing import Any

from .const import API_METRIC, ATTR_DIRECTION, ATTR_SPEED, ATTR_VALUE, CONDITION_MAP


def _dig(data: Mapping[str, Any], *path: str, default: Any = None) -> Any:
    """Read nested dict fields safely."""
    current: Any = data
    for key in path:
        if not isinstance(current, Mapping) or key not in current:
            return default
        current = current[key]
    return current


def condition_from_icon(icon_code: int | None) -> str | None:
    """Map an AccuWeather icon code to a normalized condition value."""
    if icon_code is None:
        return None
    return CONDITION_MAP.get(icon_code)


def to_utc_iso(epoch: int | float | None) -> str | None:
    """Convert epoch timestamp to UTC ISO8601 string."""
    if epoch is None:
        return None
    return datetime.fromtimestamp(epoch, tz=timezone.utc).isoformat()


def transform_current_conditions(data: Mapping[str, Any]) -> dict[str, Any]:
    """Transform current-conditions payload."""
    return {
        "condition": condition_from_icon(data.get("WeatherIcon")),
        "weather_text": data.get("WeatherText"),
        "temperature_c": _dig(data, "Temperature", API_METRIC, ATTR_VALUE),
        "apparent_temperature_c": _dig(
            data, "ApparentTemperature", API_METRIC, ATTR_VALUE
        ),
        "pressure_hpa": _dig(data, "Pressure", API_METRIC, ATTR_VALUE),
        "dew_point_c": _dig(data, "DewPoint", API_METRIC, ATTR_VALUE),
        "humidity_pct": data.get("RelativeHumidity"),
        "wind_speed_kmh": _dig(data, "Wind", ATTR_SPEED, API_METRIC, ATTR_VALUE),
        "wind_gust_kmh": _dig(data, "WindGust", ATTR_SPEED, API_METRIC, ATTR_VALUE),
        "wind_bearing_deg": _dig(data, "Wind", ATTR_DIRECTION, "Degrees"),
        "visibility_km": _dig(data, "Visibility", API_METRIC, ATTR_VALUE),
        "uv_index": data.get("UVIndex"),
        "cloud_cover_pct": data.get("CloudCover"),
        "precipitation_mm_last_hour": _dig(
            data, "PrecipitationSummary", "PastHour", API_METRIC, ATTR_VALUE
        ),
        "precipitation_type": data.get("PrecipitationType"),
    }


def transform_daily_forecast(data: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Transform daily forecast payload."""
    transformed: list[dict[str, Any]] = []
    for item in data:
        transformed.append(
            {
                "time": to_utc_iso(item.get("EpochDate")),
                "condition": condition_from_icon(item.get("IconDay")),
                "text_day": item.get("LongPhraseDay"),
                "temperature_max_c": _dig(item, "TemperatureMax", ATTR_VALUE),
                "temperature_min_c": _dig(item, "TemperatureMin", ATTR_VALUE),
                "apparent_temperature_max_c": _dig(
                    item, "RealFeelTemperatureMax", ATTR_VALUE
                ),
                "humidity_avg_pct": _dig(item, "RelativeHumidityDay", "Average"),
                "cloud_cover_pct": item.get("CloudCoverDay"),
                "precipitation_mm": _dig(item, "TotalLiquidDay", ATTR_VALUE),
                "precipitation_probability_pct": item.get("PrecipitationProbabilityDay"),
                "wind_speed_kmh": _dig(item, "WindDay", ATTR_SPEED, ATTR_VALUE),
                "wind_gust_kmh": _dig(item, "WindGustDay", ATTR_SPEED, ATTR_VALUE),
                "wind_bearing_deg": _dig(item, "WindDay", ATTR_DIRECTION, "Degrees"),
                "uv_index": _dig(item, "UVIndex", ATTR_VALUE),
            }
        )
    return transformed


def transform_hourly_forecast(data: list[Mapping[str, Any]]) -> list[dict[str, Any]]:
    """Transform hourly forecast payload."""
    transformed: list[dict[str, Any]] = []
    for item in data:
        transformed.append(
            {
                "time": to_utc_iso(item.get("EpochDateTime")),
                "condition": condition_from_icon(item.get("WeatherIcon")),
                "temperature_c": _dig(item, "Temperature", ATTR_VALUE),
                "apparent_temperature_c": _dig(item, "RealFeelTemperature", ATTR_VALUE),
                "humidity_pct": item.get("RelativeHumidity"),
                "cloud_cover_pct": item.get("CloudCover"),
                "precipitation_mm": _dig(item, "TotalLiquid", ATTR_VALUE),
                "precipitation_probability_pct": item.get("PrecipitationProbability"),
                "wind_speed_kmh": _dig(item, "Wind", ATTR_SPEED, ATTR_VALUE),
                "wind_gust_kmh": _dig(item, "WindGust", ATTR_SPEED, ATTR_VALUE),
                "wind_bearing_deg": _dig(item, "Wind", ATTR_DIRECTION, "Degrees"),
                "uv_index": item.get("UVIndex"),
            }
        )
    return transformed


def build_summary(
    current_raw: Mapping[str, Any],
    daily_raw: list[Mapping[str, Any]],
    hourly_raw: list[Mapping[str, Any]],
) -> dict[str, Any]:
    """Build a combined summary payload."""
    return {
        "current": transform_current_conditions(current_raw),
        "daily": transform_daily_forecast(daily_raw),
        "hourly": transform_hourly_forecast(hourly_raw),
    }
