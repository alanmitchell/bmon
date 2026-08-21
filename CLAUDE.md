# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Overview

BMON is a Django web application that stores and analyzes sensor/time-series data from buildings (energy use, temperatures, boiler status, etc.). It ingests readings from a variety of sensor gateways, runs calculated fields and alerts, and presents charts and reports. Django 2.2 on Python 3.11 (pinned — Django 2.x with newer Python breaks email sending; see `pyproject.toml`).

## Commands

Dependencies are managed with **uv**; the virtualenv lives at `.venv/`. Always call Python via `.venv/bin/python` (or activate the venv).

```bash
uv sync                                          # install/refresh dependencies from uv.lock
.venv/bin/python manage.py runserver             # local dev server
.venv/bin/python manage.py migrate               # apply Django (config DB) migrations
.venv/bin/python manage.py makemigrations bmsapp # after editing bmsapp/models.py
.venv/bin/python manage.py collectstatic --noinput
.venv/bin/python manage.py shell_plus            # Django shell with models preloaded (django-extensions)
```

Recurring/background jobs run through **django-extensions `runscript`**, not as management commands:

```bash
.venv/bin/python manage.py runscript main_cron            # the 5-minute cron dispatcher
.venv/bin/python manage.py runscript run_periodic_scripts # data-collection scripts only
```

Production update is `./update.sh` (git pull → uv sync → migrate → collectstatic → restart the `bmon` systemd service).

There is no test suite checked into the repo (Django's `manage.py test` runner is configured but finds no tests).

## Configuration / settings

Settings are split across three files:

- `bmon/settings_common.py` — shared Django settings for all installs (DATABASES, MIDDLEWARE, etc.). Note it does `from . import settings`, so it depends on the per-install file.
- `bmon/settings.py` — **per-install, git-ignored** (see `.gitignore`). Holds secrets, `ALLOWED_HOSTS`, API keys, `BMSAPP_NAV_LINKS`, store keys. Its tail line is `from .settings_common import *`, and any common settings can be overridden below that import.
- `bmon/settings_example.py` — the committed template to copy to `settings.py` on a new install.

When adding a setting that all installs need, add it to `settings_common.py` (or `settings_example.py` if it's install-specific), not just the local `settings.py`, since the latter isn't tracked.

## Architecture

### Two separate databases

This is the most important structural fact. BMON uses **two SQLite databases** that must not be confused:

1. **Config DB** (`bmon.sqlite`) — standard Django ORM. Holds configuration: `Building`, `Sensor`, `BldgToSensor`, `AlertCondition`, `DashboardItem`, `PeriodicScript`, `Organization`, etc. All in `bmsapp/models.py`.
2. **Reading DB** (`bmsapp/readingdb/data/bms_data.sqlite`) — the actual time-series sensor readings, accessed **not** through the ORM but through the custom `BMSdata` class in `bmsapp/readingdb/bmsdata.py` (raw `sqlite3`, one table per sensor id). Anything reading or writing sensor values goes through a `BMSdata` instance.

### Data ingress path

Sensor gateways POST readings to `store_reading*` views (`bmsapp/views.py`), routed in `bmsapp/urls.py` under `readingdb/reading/...`. There are vendor-specific endpoints: generic, Things Network / LoRaWAN (`store-things`), Radio Bridge, Beaded, Notehub. Requests must carry the `BMSAPP_STORE_KEY`.

Flow: view → `bmsapp/storereads.py` (validates store key, applies **transform functions**) → `BMSdata.insert_reading()`. LoRaWAN payloads are decoded first by `bmsapp/lora/decoder.py` (per-manufacturer decoders: `decode_elsys.py`, `decode_dragino.py`, `decode_e5.py`, `decode_modbus.py`).

**New-reading hook:** after a reading is stored, `run_new_reading_hook` (in `bmsdata.py`) spawns a daemon thread calling `Sensor.new_reading()`, which is where **alert checking** now happens (alerts are checked per-incoming-reading, not on the cron pass — see the comments in `main_cron.py`).

### Cron / scheduled work

`bmsapp/scripts/main_cron.py` is run by an OS cron job every 5 minutes and dispatches sub-tasks based on the hour / 5-minute slot: `run_periodic_scripts`, `calc_readings` (calculated fields), DB backups (`backup_django_db`, `backup_readingdb`), and `terminate_old_cron`. Each is wrapped in `suppress_errors`. Scripts live in `bmsapp/scripts/`.

### Periodic scripts (external data collection)

`bmsapp/periodic_scripts/` contains pluggable modules (ecobee, enphase, ambientweather, modbus, okofen, sensaphone, influxdb, …). They are configured per-install via `PeriodicScript` rows in the Django admin and executed by `run_periodic_scripts.py`, which typically feeds results back through `storereads`.

### Calculated fields & transforms

- **Transforms** (`bmsapp/calcs/transforms.py`) scale/convert a single incoming reading at store time, based on the `Sensor.tran_calc_function` + `function_parameters` config.
- **Calculated readings** (`bmsapp/calcs/calcreadings.py`, functions in `calcfuncs01.py`) derive new synthetic sensor values from existing ones (e.g. weather imports, degree-days). Run on a cron cadence via `calc_readings.py`. A calculated sensor has `Sensor.is_calculated=True` and is skipped by store-time transforms.

### Charts & reports

`bmsapp/reports/` — each chart type is a class (`timeseries.TimeSeries`, `histogram.Histogram`, `hourly_heatmap.HourlyHeatMap`, `dashboard.Dashboard`, `xyplot.XYplot`, `exportdata.ExportData`, …), all extending `basechart.py`. Available types are registered in `basechart.BLDG_CHART_TYPES`. `views.get_report_results` dispatches to the class named there and returns JSON that front-end JS renders. To add a chart type: add the class in `bmsapp/reports/` and register it in that list.

### HTTP APIs

`bmsapp/views_api_v1.py` and `bmsapp/views_api_v2.py` expose read APIs under `/api/v1/` and `/api/v2/` (readings, sensors, buildings, organizations). Prefer v2 for new work.

### URL conventions

`bmsapp/urls.py` uses `re_path` regex patterns. The final catch-all `views.wildcard` renders a template `bmsapp/templates/bmsapp/<name>.html` for any unmatched single-segment path — so navigation entries in `BMSAPP_NAV_LINKS` (in settings) can point at a bare template name without an explicit URL route.

## Docs

Full user/developer documentation is in `docs/` (Sphinx, published to Read the Docs). `docs/source/bmon-architecture.rst`, `calculated-fields.rst`, and `api-data-access.rst` are the most relevant deep-dives.
