"""Constants and weather condition mappings for the CLI."""

from __future__ import annotations

from typing import Final

API_METRIC: Final = "Metric"
ATTR_DIRECTION: Final = "Direction"
ATTR_SPEED: Final = "Speed"
ATTR_VALUE: Final = "Value"

CONDITION_CLASSES: Final[dict[str, list[int]]] = {
    "clear-night": [33, 34, 37],
    "cloudy": [7, 8, 38],
    "exceptional": [24, 30, 31],
    "fog": [11],
    "hail": [25],
    "lightning": [15],
    "lightning-rainy": [16, 17, 41, 42],
    "partlycloudy": [3, 4, 6, 35, 36],
    "pouring": [18],
    "rainy": [12, 13, 14, 26, 39, 40],
    "snowy": [19, 20, 21, 22, 23, 43, 44],
    "snowy-rainy": [29],
    "sunny": [1, 2, 5],
    "windy": [32],
}

CONDITION_MAP: Final = {
    icon_code: condition
    for condition, icon_codes in CONDITION_CLASSES.items()
    for icon_code in icon_codes
}
