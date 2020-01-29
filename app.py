from flask import Flask 
from flask import Flask, flash, redirect, render_template, request,session,abort
import pyodbc 
import os

app = Flask(__name__)

conn = pyodbc.connect('DRIVER={PostgreSQL Unicode};SERVER=10.4.28.183;DATABASE=postgres;UID=postgres;PWD=qwe1234*')
crsr = conn.cursor()


def get_product(conn):
    try:
        cnxn = conn.cursor()
        cnxn.execute('select * from products where productid = 24596')
        rows = cnxn.fetchall()
        return rows
    except Exception as err:
        print(err)

@app.route('/products')
def products():
    retorno = get_product(conn)
    if retorno : 
        print(retorno)
        return 'trae esa vuelta'
    else:
        return 'no trae nada'

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
    else:
        return "hablame "

@app.route('/login', methods=['POST'])
def do_admin_login():
    print (request.form)
    if request.form['password'] == 'password' and  request.form['username'] == 'admin':
        session['logged_in'] = True
        print ('obvio se logueo')
    else:
     print('te equivocaste')
     #flash('Te equivocaste marditooo')
     return home()

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return home()  

@app.route('/example')
def example():
    return 'other route'

@app.route('/users/<int:id>')
def userById(id):
    return 'bienvenido usuario {}'.format(id)


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='localhost', port=8080)





