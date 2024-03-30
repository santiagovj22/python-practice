# SOPHIA Asset Service

A Microservice within the SOPHIA infrastructure to manage assets, their identifiers, attributes and
relations between them. Since SOPHIA is a distributed service system (aka 'hybrid cloud'), it also
features synchronization with other asset_service instances


## Getting Started

the asset service is designed to run in multiple instances asynchronously, therefore UUIDs are used as
primary identitfiers for all database entities.


### Prerequisites

A working instance of a PostgreSQL database server is required to run the SOPHIA asset service.
Also, a Python3 environment will be used to run the application


### Auto Installation
Run setup.sh to automatically install asset_service on your target machine.
In case the automagic installer does not fir for your environment, the following chapters describe
the basic steps to set up the application:


### Python Environment

Create Python virtual environment
```
python3 -m venv venv
```

Activate the environment inside the setup shell
```
source venv/bin/activate
```

install current pip and all required Python packages
```
pip install --upgrade pip
pip install -r requirements.txt
```


### Application configuration

create a copy of `config/app_conf.example.py` in `config/app_conf.py` and adjust the settings there to
fit your database server etc.


### Database setup

Make sure the PostgreSQL database and user exist as configured in `config/app_conf.py`.
The Postgres Server will need to have the UUID extension loaded into the database. As database superuser
run the following SQL statement inside the asset-service's database environment:
```
CREATE EXTENSION "uuid-ossp";
```
inside the activated python venv in the asset_service project root directory, run the alembic database
setup as follows:
```
flask db upgrade
```

You might want to load initial SQL data to the database to populate it with some types / classes.
Use the data provided in `config/data` to preload some data
```
\copy assetclasses FROM config/data/assetclasses.csv CSV HEADER DELIMITER ';';
```


## Using the API
The application provides a RESTful API to other applications. It is self-documenting. While the server
is running, you will find the API documentation at the address [http://server:port/api/version/doc] e.g. [http://localhost:5000/api/v1.0/doc]
