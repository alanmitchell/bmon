#!/bin/bash
# Script to update BMON to the most recent version,
# applying migrations and copying static files to
# the static serving application.
git pull
pipenv run ./manage.py migrate
pipenv run ./manage.py collectstatic --noinput
sudo systemctl restart bmon
