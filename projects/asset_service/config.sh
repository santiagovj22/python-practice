#!/bin/bash
# TODO: make use of pysetup mechanisms

PYENV_DIR="venv"
SERVICE_NAME=asset_service
ASSYNC_SERVICE_NAME=asset_sync
SERVICE_DESC="Sophia Asset Service"
ASSYNC_SERVICE_DESC="Sophia Asset Service Sync Worker"
SERVICE_FILE="$SERVICE_NAME.service"
ASSYNC_SERVICE_FILE="$ASSYNC_SERVICE_NAME.service"
ASSYNC_TIMER_FILE="$ASSYNC_SERVICE_NAME.timer"
SERVICE_FILE_FULLPATH="/etc/systemd/system/$SERVICE_FILE"
ASSYNC_SERVICE_FILE_FULLPATH="/etc/systemd/system/$ASSYNC_SERVICE_FILE"
ASSYNC_TIMER_FILE_FULLPATH="/etc/systemd/system/$ASSYNC_TIMER_FILE"
#SERVICE_LOG="/var/log/$SERVICE_NAME.log"
SERVICE_USER=sophia_backend
SERVICE_PORT=10181

# TODO: get this data from some sort of config-management (to be defined...)
DB_HOST="localhost"
DB_USER="assetservice"
DB_PASS="asset"
DB_NAME="assetservice"
DB_STRING="postgres://$DB_USER:$DB_PASS@$DB_HOST/$DB_NAME"

APACHE_CONF="/etc/apache2/sites-available/sophia.conf"

FAIL=0
