#!/bin/bash
# Script to update BMON to the most recent version,
# applying migrations and copying static files to
# the static serving application.
git pull
uv sync
.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput
sudo systemctl restart bmon
