#!/bin/sh

# echo "Matando el container"
# sudo kill $(sudo lsof -t -i:5432)

echo "Reiniciando el container"
docker restart data_service_db_1 
echo "-************************-"
echo "Entrando al environment"
source venv/bin/activate
echo "Python version"
python3 --version
echo "Corriendo variables de entorno"
export FLASK_ENV=development
export FLASK_APP=app.py
export FLASK_RUN_PORT=5001
echo "corriendo el server"
flask run 