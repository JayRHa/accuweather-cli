"""Command line interface for AccuWeather."""

from __future__ import annotations

import argparse
import asyncio
import json
import os
import sys
from collections.abc import Sequence
from typing import Any

from accuweather import (
    AccuWeather,
    ApiError,
    InvalidApiKeyError,
    InvalidCoordinatesError,
    RequestsExceededError,
)
from aiohttp import ClientError, ClientSession, ClientTimeout

from .transform import (
    build_summary,
    transform_current_conditions,
    transform_daily_forecast,
    transform_hourly_forecast,
)

DEFAULT_DAYS = 5
DEFAULT_HOURS = 12


class CliInputError(ValueError):
    """Raised for invalid CLI argument combinations."""


def build_parser() -> argparse.ArgumentParser:
    """Build the argument parser."""
    parser = argparse.ArgumentParser(
        prog="accuweather",
        description=("High-signal CLI for AccuWeather weather and forecast data"),
    )
    parser.add_argument(
        "--api-key",
        default=os.getenv("ACCUWEATHER_API_KEY"),
        help="AccuWeather API key (or env ACCUWEATHER_API_KEY)",
    )
    parser.add_argument("--location-key", help="AccuWeather location key")
    parser.add_argument("--lat", type=float, help="Latitude")
    parser.add_argument("--lon", type=float, help="Longitude")
    parser.add_argument("--language", default="en", help="Language code, e.g. de")
    parser.add_argument(
        "--json", dest="json_output", action="store_true", help="Output as JSON"
    )

    subparsers = parser.add_subparsers(dest="command", required=True)

    subparsers.add_parser("location", help="Resolve location key from coordinates")
    subparsers.add_parser("current", help="Get current conditions")

    daily_parser = subparsers.add_parser("daily", help="Get daily forecast")
    daily_parser.add_argument("--days", type=int, default=DEFAULT_DAYS)

    hourly_parser = subparsers.add_parser("hourly", help="Get hourly forecast")
    hourly_parser.add_argument("--hours", type=int, default=DEFAULT_HOURS)

    summary_parser = subparsers.add_parser(
        "summary", help="Get current + daily + hourly weather"
    )
    summary_parser.add_argument("--days", type=int, default=DEFAULT_DAYS)
    summary_parser.add_argument("--hours", type=int, default=DEFAULT_HOURS)

    return parser


def validate_args(args: argparse.Namespace) -> None:
    """Validate argument combinations."""
    if not args.api_key:
        raise CliInputError("API key missing. Use --api-key or ACCUWEATHER_API_KEY.")

    lat_is_set = args.lat is not None
    lon_is_set = args.lon is not None

    if lat_is_set != lon_is_set:
        raise CliInputError("Use --lat and --lon together.")

    if args.command == "location":
        if not (lat_is_set and lon_is_set):
            raise CliInputError("`location` requires --lat and --lon.")
        return

    if args.location_key is None and not (lat_is_set and lon_is_set):
        raise CliInputError(
            "Provide --location-key or coordinates via --lat/--lon."
        )

    if hasattr(args, "days") and args.days <= 0:
        raise CliInputError("--days must be greater than 0.")

    if hasattr(args, "hours") and args.hours <= 0:
        raise CliInputError("--hours must be greater than 0.")


def _render_table(headers: list[str], rows: list[list[Any]]) -> str:
    """Render rows as a plain text table."""
    normalized_rows = [["-" if value is None else str(value) for value in row] for row in rows]
    widths = [len(h) for h in headers]

    for row in normalized_rows:
        for index, value in enumerate(row):
            widths[index] = max(widths[index], len(value))

    header_line = " | ".join(header.ljust(widths[i]) for i, header in enumerate(headers))
    separator = "-+-".join("-" * width for width in widths)
    body = [" | ".join(value.ljust(widths[i]) for i, value in enumerate(row)) for row in normalized_rows]

    return "\n".join([header_line, separator, *body])


def _format_location(location: dict[str, Any]) -> str:
    key = location.get("location_key")
    name = location.get("location_name")
    if key and name:
        return f"{name} ({key})"
    if key:
        return str(key)
    return name or "unknown"


def print_human(command: str, payload: dict[str, Any]) -> None:
    """Print result in human-readable format."""
    print(f"Location: {_format_location(payload['location'])}")

    if command == "location":
        print(f"Location key: {payload['location']['location_key']}")
        print(f"Location name: {payload['location'].get('location_name') or '-'}")
        return

    if command == "current":
        current = payload["current"]
        fields = [
            ("Condition", "condition"),
            ("Weather text", "weather_text"),
            ("Temperature (C)", "temperature_c"),
            ("Feels like (C)", "apparent_temperature_c"),
            ("Humidity (%)", "humidity_pct"),
            ("Pressure (hPa)", "pressure_hpa"),
            ("Wind (km/h)", "wind_speed_kmh"),
            ("Wind gust (km/h)", "wind_gust_kmh"),
            ("UV index", "uv_index"),
        ]
        for label, key in fields:
            value = current.get(key)
            print(f"{label}: {'-' if value is None else value}")
        return

    if command == "daily":
        rows = [
            [
                item.get("time"),
                item.get("condition"),
                item.get("temperature_max_c"),
                item.get("temperature_min_c"),
                item.get("precipitation_probability_pct"),
                item.get("wind_speed_kmh"),
            ]
            for item in payload["daily"]
        ]
        print(
            _render_table(
                [
                    "time(UTC)",
                    "condition",
                    "temp_max_c",
                    "temp_min_c",
                    "precip_prob_%",
                    "wind_kmh",
                ],
                rows,
            )
        )
        return

    if command == "hourly":
        rows = [
            [
                item.get("time"),
                item.get("condition"),
                item.get("temperature_c"),
                item.get("precipitation_probability_pct"),
                item.get("wind_speed_kmh"),
            ]
            for item in payload["hourly"]
        ]
        print(
            _render_table(
                ["time(UTC)", "condition", "temp_c", "precip_prob_%", "wind_kmh"],
                rows,
            )
        )
        return

    if command == "summary":
        current = payload["current"]
        print("Current:")
        print(
            f"  {current.get('condition')} | {current.get('temperature_c')} C | "
            f"humidity {current.get('humidity_pct')}% | wind {current.get('wind_speed_kmh')} km/h"
        )

        daily_rows = [
            [
                item.get("time"),
                item.get("condition"),
                item.get("temperature_max_c"),
                item.get("temperature_min_c"),
            ]
            for item in payload["daily"]
        ]
        print("\nDaily:")
        print(_render_table(["time(UTC)", "condition", "max_c", "min_c"], daily_rows))

        hourly_rows = [
            [item.get("time"), item.get("condition"), item.get("temperature_c")]
            for item in payload["hourly"]
        ]
        print("\nHourly:")
        print(_render_table(["time(UTC)", "condition", "temp_c"], hourly_rows))


def _build_location_payload(weather: AccuWeather, lat: float | None, lon: float | None) -> dict[str, Any]:
    return {
        "location_key": weather.location_key,
        "location_name": weather.location_name,
        "latitude": lat,
        "longitude": lon,
    }


async def run_command(args: argparse.Namespace) -> dict[str, Any]:
    """Execute the selected command."""
    timeout = ClientTimeout(total=20)

    async with ClientSession(timeout=timeout) as session:
        weather = AccuWeather(
            args.api_key,
            session,
            latitude=args.lat,
            longitude=args.lon,
            location_key=args.location_key,
            language=args.language,
        )

        if args.command == "location":
            async with asyncio.timeout(20):
                await weather.async_get_location()
            return {
                "command": args.command,
                "location": _build_location_payload(weather, args.lat, args.lon),
                "requests_remaining": weather.requests_remaining,
            }

        if args.command == "current":
            async with asyncio.timeout(20):
                current_raw = await weather.async_get_current_conditions(
                    language=args.language
                )
            return {
                "command": args.command,
                "location": _build_location_payload(weather, args.lat, args.lon),
                "current": transform_current_conditions(current_raw),
                "requests_remaining": weather.requests_remaining,
            }

        if args.command == "daily":
            async with asyncio.timeout(20):
                daily_raw = await weather.async_get_daily_forecast(
                    days=args.days,
                    language=args.language,
                )
            return {
                "command": args.command,
                "location": _build_location_payload(weather, args.lat, args.lon),
                "daily": transform_daily_forecast(daily_raw),
                "requests_remaining": weather.requests_remaining,
            }

        if args.command == "hourly":
            async with asyncio.timeout(20):
                hourly_raw = await weather.async_get_hourly_forecast(
                    hours=args.hours,
                    language=args.language,
                )
            return {
                "command": args.command,
                "location": _build_location_payload(weather, args.lat, args.lon),
                "hourly": transform_hourly_forecast(hourly_raw),
                "requests_remaining": weather.requests_remaining,
            }

        async with asyncio.timeout(30):
            current_raw = await weather.async_get_current_conditions(language=args.language)
            daily_raw = await weather.async_get_daily_forecast(
                days=args.days,
                language=args.language,
            )
            hourly_raw = await weather.async_get_hourly_forecast(
                hours=args.hours,
                language=args.language,
            )

        summary = build_summary(current_raw, daily_raw, hourly_raw)
        return {
            "command": args.command,
            "location": _build_location_payload(weather, args.lat, args.lon),
            **summary,
            "requests_remaining": weather.requests_remaining,
        }


def main(argv: Sequence[str] | None = None) -> int:
    """CLI entry point."""
    parser = build_parser()
    args = parser.parse_args(argv)

    try:
        validate_args(args)
        payload = asyncio.run(run_command(args))
    except CliInputError as error:
        print(f"Input error: {error}", file=sys.stderr)
        return 2
    except InvalidApiKeyError:
        print("Error: Invalid API key.", file=sys.stderr)
        return 2
    except RequestsExceededError:
        print("Error: Request limit exceeded.", file=sys.stderr)
        return 2
    except InvalidCoordinatesError as error:
        print(f"Error: {error}", file=sys.stderr)
        return 2
    except (ApiError, ClientError, TimeoutError) as error:
        print(f"Error while calling AccuWeather API: {error}", file=sys.stderr)
        return 1

    if args.json_output:
        print(json.dumps(payload, ensure_ascii=False, indent=2, sort_keys=True))
    else:
        print_human(args.command, payload)

    return 0
