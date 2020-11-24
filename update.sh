#!/bin/bash
# Script to update BMON to the most recent version,
# applying migrations and copying static files to
# the static serving application.
git pull
source bmonenv/bin/activate
./manage.py migrate
./manage.py collectstatic --noinput
deactivate
sudo systemctl restart bmon
