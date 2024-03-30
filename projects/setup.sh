#!/bin/bash

# -- setup.sh --

# this setup script tries to set up all required packages
# and system dependencies to create a runnable instance
# of the application.
# As it is very Debian/Ubuntu specicfic currently, no
# other platforms are supported yet, but might be
# integrated at a later date.
# The Commands in this script should be designed in a way,
# that it can be re-run after each checkout of the GIT repo.
#
# By its nature, this script will use operating system mechanisms
# to install software on the system it is running on. This will
# in most cases require the script running user to be allowed to
# run the 'apt-get' command as root using the 'sudo' command.
# Please make sure an apropirate configuration
# (e.g. entry in sudoers file allowing to execute apt-get) is set
# up.

# EKU Power Drives GmbH 2019, Kristian Binder <kristian.binder@ekupd.com>

source config.sh

echo "=== Package Setup ==="
echo "installing system packets and external dependencies to
make this package runnable"

# --- stop running instances of this service ---
sudo systemctl stop $SERVICE_NAME


# --- generate local config file ---
if [ ! -f "config/app_conf.py" ]; then
  cp config/app_conf.example.py  config/app_conf.py
fi

if [ ! -f "config/gunicorn_conf.py" ]; then
  cp config/gunicorn_conf.example.py  config/gunicorn_conf.py
fi

sed -i -e 's|"postgres://.*|"'$DB_STRING'",|' config/app_conf.py

if [ ! -z $SERVICE_LOG ]; then	

  sed -i -e "s|'/var/log/something.log'|'$SERVICE_LOG'|" config/app_conf.py

  if [ ! -f $SERVICE_LOG ]; then
  	sudo touch $SERVICE_LOG	
  fi

  sudo chown :$SERVICE_USER $SERVICE_LOG
  sudo chmod 660 $SERVICE_LOG
fi

# --- required Debian packets ---
REQ_DEBS="python3 python3-venv python3-pip"
if [ -f "requirements.debian" ]; then
  REQ_DEBS="$REQ_DEBS $(cat requirements.debian)"
fi

sudo apt-get -y install $REQ_DEBS
if [ $? != 0 ]; then
  FAIL=$FAIL+1
  echo " WARN: cannot install the required Debian packages. This might cause failure"
fi


# --- build and use Python environment ---
if [ ! -d $PYENV_DIR ]; then
  python3 -m venv $PYENV_DIR
fi;

if [ ! -x "$PYENV_DIR/bin/python" ] || [ ! -x "$PYENV_DIR/bin/pip" ]; then
  echo " WARN: found a venv directory ('$PYENV_DIR') but it seems fishy - rebuild"
  rm -rf $PYENV_DIR
  python3 -m venv $PYENV_DIR
fi

source "$PYENV_DIR/bin/activate"

pip install --upgrade pip
if [ $? != 0 ]; then
  FAIL=$FAIL+1
  echo " WARN: cannot upgrade pip"
fi

# --- install Python requirements ---
if [ -f requirements.txt ]; then
  pip install -r requirements.txt
  if [ $? != 0 ]; then
    FAIL=$FAIL+1
    echo "WARN: cannot install requirements from requirements.txt"
  fi
fi


# --- setup database ---
if [ ! -z $DB_USER ]; then
  psql -q -l -t $DB_STRING
  if [ $? != 0 ]; then
    echo " INFO: DB not existing - will try to create User and DB"
    # TODO: this will only work on localhost database server .. find a better solution for the future!
    echo "CREATE ROLE $DB_USER WITH LOGIN PASSWORD '$DB_PASS';" | sudo su -l postgres -c psql
    echo "CREATE DATABASE $DB_NAME OWNER $DB_USER;" | sudo su -l postgres -c psql
    echo "GRANT ALL ON DATABASE $DB_NAME TO $DB_USER;"
    echo "CREATE EXTENSION \"uuid-ossp\";" | sudo su -l postgres -c "psql -d $DB_NAME"
    echo "CREATE EXTENSION IF NOT EXISTS timescaledb VERSION '2.1.0';" | sudo su -l postgres -c "psql -d $DB_NAME"
  
    sudo sed -i '/local\ +all\ +all/s/[a-zA-Z0-9]+$/md5/p' /etc/postgresql/*/main/pg_hba.conf

    if [ $? != 0 ]; then
      FAIL=$FAIL+1
      echo " WARN: cannot create database"
    fi

  fi

  export LANG=C.UTF-8

  flask db upgrade
  if [ $? != 0 ]; then
    FAIL=$FAIL+1
    echo " WARN: Flask database update did not work"
  fi

  if [ -f config/db_initialdata.sql ]; then
    cat config/db_initialdata.sql | psql $DB_STRING
    if [ $? != 0 ]; then
      FAIL=$FAIL+1
      echo " WARN: Error while inserting initial data"
    fi
  fi
fi

deactivate

echo "Setting up systemd Service"
if [ ! -f $SERVICE_FILE_FULLPATH ]; then
  echo "[Unit]
Description=$SERVICE_DESC
After=syslog.target postgresql.service

[Service]
Type=simple
User=$SERVICE_USER
WorkingDirectory=`pwd`
ExecStart=`pwd`/venv/bin/gunicorn app:app --config python:config.gunicorn_conf
StandardOutput=syslog
StandardError=syslog
SyslogIdentifier=$SERVICE_NAME

[Install]
WantedBy=multi-user.target
" > $SERVICE_FILE_FULLPATH
fi

sudo chown -R $SERVICE_USER:$SERVICE_USER `pwd`

# --- create system service in systemd and start it ---
#sudo systemctl link "`pwd`/$SERVICE_FILE"
sudo systemctl enable $SERVICE_FILE
sudo systemctl start $SERVICE_FILE
sudo systemctl status $SERVICE_FILE

if [ -f $APACHE_CONF ]; then
  sudo sed -i -e '\|^</VirtualHost>|i \
        <Location "/'$SERVICE_NAME'/">\
            ProxyPass  "http://127.0.0.1:'$SERVICE_PORT'/"\
            ProxyPassReverse "http://127.0.0.1:'$SERVICE_PORT'/"\
        </Location>' $APACHE_CONF
fi

if [ $FAIL != 0 ]; then
  echo " Some things went wrong - please check output"
  exit 1
fi
