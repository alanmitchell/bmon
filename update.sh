#!/bin/sh
# Script to update BMON to the most recent version,
# applying migrations and copying static files to
# the static serving application.
../apache2/bin/stop
git pull
./manage.py migrate
./manage.py collectstatic --noinput
../apache2/bin/restart
