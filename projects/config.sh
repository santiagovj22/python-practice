#!/bin/bash

# -- setup.sh --

# TODO: make use of pysetup mechanisms

PYENV_DIR="venv"
SERVICE_NAME=data_service
SERVICE_DESC="Sophia Data Service"
SERVICE_FILE="$SERVICE_NAME.service"
SERVICE_FILE_FULLPATH="/etc/systemd/system/$SERVICE_FILE"
#SERVICE_LOG="/var/log/$SERVICE_NAME.log"
SERVICE_USER=sophia_backend
SERVICE_PORT=10182

# TODO: get this data from some sort of config-management (to be defined...)
DB_HOST="localhost"
DB_USER="dataservice"
DB_PASS="data"
DB_NAME="dataservice"
DB_STRING="postgres://$DB_USER:$DB_PASS@$DB_HOST/$DB_NAME"

APACHE_CONF="/etc/apache2/sites-available/sophia.conf"

FAIL=0
