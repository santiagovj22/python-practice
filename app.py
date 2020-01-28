from flask import Flask 
from flask import Flask, flash, redirect, render_template, request,session,abort
import pyodbc 

app = Flask(__name__)
# #[ODBC Driver 17 for SQL Server]
# Description=Microsoft ODBC Driver 17 for SQL Server
# Driver=/opt/microsoft/msodbcsql17/lib64/libmsodbcsql-17.4.so.2.1
# UsageCount=1

conn = pyodbc.connect('DRIVER={PostgreSQL Unicode};SERVER=10.4.28.183;DATABASE=postgres;UID=postgres;PWD=qwe1234*')
crsr = conn.cursor()


def get_product(conn):
    try:
        cnxn = conn.cursor()
        cnxn.execute('select * from products')
        rows = cnxn.fetchall()
        return rows
    except Exception as err:
        print(err)

@app.route('/')
def home():
    retorno = get_product(conn)
    if retorno : 
        print(retorno)
        return 'helo'
    else:
        return 'bye'

    # if not session.get('logged_in'):
    #     return render_template('login.html')
    # else:
    #    return 'Hello Boss!'

@app.route('/login', methods=['POST'])
def do_admin_login():
    print (request.form)
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

# @app.route('/num')
# def getAllProducts(data):
#      for i in data:
#          print (data[i])
#          return getAllProducts(data)        


if __name__ == "__main__":
  
    app.run(debug=True,host='localhost', port=4000)





