# Commands that need to be run to upgrade to uv

git pull
sudo systemctl stop bmon
git checkout uv-package-mgr
rm -rf env/
uv sync
# edit crontab
# edit /etc/systemd/system/bmon.service
sudo systemctl daemon-reload
sudo systemctl restart bmon
