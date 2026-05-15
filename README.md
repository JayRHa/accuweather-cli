<!-- unified-readme:start -->
    <div align="center">

    # AccuWeather CLI

    **CLI tool for fetching weather data and forecasts from AccuWeather.**

    Build. Automate. Share.

    [![GitHub stars](https://img.shields.io/github/stars/JayRHa/AccuWeatherCLI?style=for-the-badge&logo=github&color=f4c542)](https://github.com/JayRHa/AccuWeatherCLI/stargazers)
[![GitHub forks](https://img.shields.io/github/forks/JayRHa/AccuWeatherCLI?style=for-the-badge&logo=github&color=4078c0)](https://github.com/JayRHa/AccuWeatherCLI/network/members)
[![GitHub issues](https://img.shields.io/github/issues/JayRHa/AccuWeatherCLI?style=for-the-badge&logo=github&color=d73a4a)](https://github.com/JayRHa/AccuWeatherCLI/issues)
[![Contributors](https://img.shields.io/github/contributors/JayRHa/AccuWeatherCLI?style=for-the-badge&logo=github&color=28a745)](https://github.com/JayRHa/AccuWeatherCLI/graphs/contributors)

    ---

    `CLI Tool` | `Python` | `Public` | `Maintained`

    </div>

    ## What is this?

    This repository contains cLI tool for fetching weather data and forecasts from AccuWeather.

    > Browse the documentation below for setup notes, usage details, and project-specific context.

    ---

    ## Quick Start

    1. Review the project documentation below.
2. Clone the repository:

   ```bash
   git clone https://github.com/JayRHa/AccuWeatherCLI.git
   ```

3. Follow the setup, deployment, or usage notes in the preserved documentation section.

    ---
    <!-- unified-readme:end -->


## Existing Documentation

<div align="center">
  <h1>AccuWeather CLI</h1>
  <p><strong>Elegant terminal weather. Scriptable JSON. Production-ready workflows.</strong></p>
  <p>
    <img src="https://img.shields.io/badge/python-3.11%2B-2d7ff9?style=for-the-badge" alt="Python 3.11+">
    <img src="https://img.shields.io/badge/interface-CLI-0f172a?style=for-the-badge" alt="CLI">
    <img src="https://img.shields.io/badge/output-text%20%7C%20json-0ea5e9?style=for-the-badge" alt="Text and JSON output">
    <img src="https://img.shields.io/badge/automation-ready-16a34a?style=for-the-badge" alt="Automation ready">
  </p>
</div>

## Overview

`accuweather` is a high-signal command line tool for:

- current conditions
- daily and hourly forecasts
- clean machine-readable JSON for pipelines
- fast terminal-first human output

## 60-Second Quickstart

```bash
python3 -m venv .venv
source .venv/bin/activate
python3 -m pip install -e .
export ACCUWEATHER_API_KEY="<YOUR_API_KEY>"

accuweather --lat 52.52 --lon 13.405 location
accuweather --location-key 178087 current
accuweather --location-key 178087 summary --json
```

## Why It Feels Great To Use

- Single command surface: `accuweather`
- Strict argument validation with clear errors
- Human view for operators, JSON view for automation
- Flexible location model: `--location-key` or `--lat/--lon`
- Predictable exit codes for CI and scripts

## Install

```bash
python3 -m pip install -e .
```

If your Python is externally managed, use a virtualenv (recommended).

## Authentication

Use one of these:

```bash
accuweather --api-key "<KEY>" --location-key 178087 current
```

```bash
export ACCUWEATHER_API_KEY="<KEY>"
accuweather --location-key 178087 current
```

## Command Matrix

| Command | Purpose | Common flags |
| --- | --- | --- |
| `location` | Resolve location key from coordinates | `--lat --lon` |
| `current` | Current weather conditions | `--location-key`, `--json` |
| `daily` | Daily forecast | `--days`, `--json` |
| `hourly` | Hourly forecast | `--hours`, `--json` |
| `summary` | Current + daily + hourly in one payload | `--days --hours --json` |

## Usage Examples

### Resolve location key

```bash
accuweather --lat 52.52 --lon 13.405 location
accuweather --lat 40.7128 --lon -74.0060 location --json
```

### Current conditions

```bash
accuweather --location-key 178087 current
accuweather --location-key 178087 current --language de --json
```

### Forecasts

```bash
accuweather --location-key 178087 daily --days 7
accuweather --location-key 178087 hourly --hours 24
accuweather --location-key 178087 summary --days 7 --hours 24 --json
```

## Automation Recipes

Current temperature for shell scripts:

```bash
accuweather --location-key 178087 summary --json | jq -r '.current.temperature_c'
```

Daily max temperatures:

```bash
accuweather --location-key 178087 daily --days 5 --json \
  | jq -r '.daily[] | [.time, .temperature_max_c] | @tsv'
```

## Exit Codes

| Code | Meaning |
| --- | --- |
| `0` | Success |
| `1` | API/network/runtime error |
| `2` | Input/auth/rate-limit error |

## Troubleshooting

`Input error: API key missing`
Use `--api-key` or set `ACCUWEATHER_API_KEY`.

`Input error: Use --lat and --lon together`
Provide both coordinates as a pair.

`Error: Invalid API key`
Check your key and permissions.

`Error: Request limit exceeded`
Provider rate limit hit; retry later.

## Developer Notes

Run from source:

```bash
PYTHONPATH=src python3 -m accuweather_cli --help
```

Compile check:

```bash
python3 -m compileall -q src tests
```

Tests:

```bash
PYTHONPATH=src python3 -m pytest -q
```

## Project Structure

```text
src/accuweather_cli/
  cli.py           # parsing, command execution, output rendering
  transform.py     # normalization layer
  const.py         # condition mapping and constants
  __main__.py      # python -m entrypoint
tests/
  test_transform.py
```

## Security

- Never commit API keys.
- Prefer environment variables in CI/CD.
- Rotate keys immediately if exposed.
