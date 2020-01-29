from flask import Flask

app = Flask(__name__)

@app.route("/")
def index():
    return "Hello World!"

@app.route('/articulos/')
def articulos():
    return 'Lista de artículos'

@app.route('/users')

@app.route("/articulos/<int:id>")
def mostrar_ariculo(id):
	return 'Vamos a mostrar el artículo con id:{}'.format(id)	

if __name__ == "__main__" :
    app.run(host='0.0.0.0', port=3000)