#!/bin/sh
../apache2/bin/stop
git pull
./manage.py migrate
./manage.py collectstatic
../apache2/bin/restart
