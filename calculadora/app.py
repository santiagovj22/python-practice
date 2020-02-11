from flask import Flask, request, render_template
app = Flask(__name__)

@app.route('/')
def init() :
    return 'calculadora en la ruta operaciones'

@app.route('/operaciones', methods = ["GET", "POST"])
def calculadora():    
    if request.method == "POST" :
        num1 = request.form.get("num1")
        num2 = request.form.get("num2")
        operador = request.form.get("operador")

        try:
            resultado = eval(num1 + operador + num2)
        except:

            return  'no se pudo realizar la operacion'

        return render_template("resultado.html",
                                num1=num1,
                                num2=num2,
                                operador=operador,
                                resultado=resultado)    
    else:
        return render_template("index.html")                            

if __name__ == "__main__" :
    app.run(host = 'localhost', port = 3000)