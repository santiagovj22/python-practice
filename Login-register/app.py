from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
import pyodbc
import json
import bcrypt

conn = pyodbc.connect('DRIVER={PostgreSQL Unicode};SERVER=10.4.28.183;DATABASE=postgres;UID=postgres;PWD=developer2020') #driver connection

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mamamelamamamelavalaropa' #secret key 
Bootstrap(app)

class LoginForm(FlaskForm): #generate inputs login
    username = StringField('username', validators=[InputRequired(), Length(min=4, max = 80)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max = 80)])
    remember = BooleanField('remember me')

class RegisterForm(FlaskForm): #generate inputs register
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(),Length(min=4, max = 80)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max = 80)])

def extraction_data(conn):
    cnxn = conn.cursor()
    cnxn.execute('select userid, email, password from users where status = 1') #query for show all users
    data = cnxn.fetchall()
    cnxn.commit()

    return data

def convert_json(data): #function for convert to json, in the iterator use the index corresponding to the rows in a DB
    data_user = []
    for i in data:
        _json = {
            'userid' : i[0],
            'email': i[1],
            'password': i[2]
        }

        #print(_json)
        data_user.append(_json) #insert data in list
    return data_user


@app.route('/')
def index():
    data=extraction_data(conn)
    users=convert_json(data) #pass the params to convert
    
    return json.dumps({"Users" : users}) 
    #return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

      #if form.validate_on_submit():
       
         
       # print( form.username.data + ' ' + form.password.data )

    return render_template('login.html', form = form)

@app.route('/register', methods=["GET", "POST"])
def signup():
    form = RegisterForm() #instance an object from a class registerForm

    if form.validate_on_submit(): #if the form send good
        cnxn=conn.cursor()#necesary for make a query
        password = form.password.data.encode()#password must be enconde to binary
        salt = bcrypt.gensalt(12)
        hashed = bcrypt.hashpw(password, salt)# pass hashed

        if bcrypt.checkpw(password,hashed):
            print('si es')
        else:
            print('no es')    

        insert_user ='''INSERT INTO users( name,email,password, roleid, lastname, id, address,status) VALUES(?,?,?,?,?,?,?,?)''' #query for save in the database
        cnxn.execute(insert_user, form.username.data, form.email.data, hashed, 1, '', '','',1) #execute the query
        cnxn.commit()#exit connection

        print(form.email.data + ' ---> user has been created') 

    return render_template('signup.html', form = form) #shows the templates

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port = 3000)    
