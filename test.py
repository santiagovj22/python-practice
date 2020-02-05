
from flask import Flask

app = Flask(__name__)

@app.route("/suma", methods=["GET","POST"])
def sumar():
    if request.method == "POST":
        num1=request.form.get("num1")
        num2=request.form.get("num2")
        print(num1)
    else:
        return render_template('suma.html')    

if __name__ == "__main__":
    app.run(host='localhost', port=3000)
    