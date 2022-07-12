#!/bin/bash
# Script to update BMON to the most recent version,
# applying migrations and copying static files to
# the static serving application.
git pull
env/bin/pip install -r requirements.txt --upgrade
env/bin/python manage.py migrate
env/bin/python manage.py collectstatic --noinput
sudo systemctl restart bmon
