from flask import Flask 
from flask import Flask, flash, redirect, render_template, request,session,abort
import os
import sys

app = Flask(__name__)

@app.route('/')
def home():
    if not session.get('logged_in'):
        return render_template('login.html')
       
    else:
       return 'Hello Boss!'

@app.route('/login', methods=['POST'])
def do_admin_login():
    if request.form['password'] == 'password' and request.form['username'] == 'admin':
        session['logged_in'] = True
    else:
     flash('Te equivocaste marditooo')
     return home()

@app.route('/logout')
def logout():
    session['logged_in'] = False
    return home()  

@app.route('/example')
def example():
    return 'other route'

data = [0,1,2,3,4,5,6]

 for j in data :
    print (data[j])

@app.route('/num')
def getAllProducts(data):
     for i in data:
         print (data[i])
         return getAllProducts(data)        


if __name__ == "__main__":
    app.secret_key = os.urandom(12)
    app.run(debug=True,host='localhost', port=4000)
