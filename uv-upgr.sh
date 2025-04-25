#!/bin/bash
# Commands that need to be run to upgrade to uv

# install uv
curl -LsSf https://astral.sh/uv/install.sh | sh

sudo systemctl stop bmon

rm -rf env/
uv sync

.venv/bin/python manage.py migrate
.venv/bin/python manage.py collectstatic --noinput

echo "Edit Crontab and Edit /etc/systemd/system/bmon.service and then press Enter"
read

sudo systemctl daemon-reload
sudo systemctl restart bmon
