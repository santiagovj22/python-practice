#!/bin/bash

# Install Timescale package
sudo sh -c "echo 'deb https://packagecloud.io/timescale/timescaledb/debian/ `lsb_release -c -s` main' > /etc/apt/sources.list.d/timescaledb.list"
wget --quiet -O - https://packagecloud.io/timescale/timescaledb/gpgkey | sudo apt-key add -
sudo apt-get update

# Now install appropriate package for PG version
sudo apt-get install timescaledb-2-2.1.0-postgresql-11

# make some database settings for timescale. If you want to use default values which are set by timescaledb-tune then use "timescaledb-tune --quiet --yes"
sudo timescaledb-tune
sudo service postgresql restart





