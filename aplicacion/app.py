from flask import Flask
from flask import request, render_template, abort
from flask_bootstrap import Bootstrap
app = Flask(__name__)
Bootstrap(app)
@app.route('/')

@app.route('/<nombre>')
def saluda(nombre=None) :
    return render_template("template1.html", nombre=nombre)

if __name__ == "__main__":
    app.run(host='localhost', port=3000)
    