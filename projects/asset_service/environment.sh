#!/bin/sh
echo "Entrando al environment"
source venv/bin/activate
echo "Python version"
python3 --version
echo "Corriendo variables de entorno"
export FLASK_ENV=development
export FLASK_APP=app.py
echo "corriendo el server"
flask run 