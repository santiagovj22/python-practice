from flask import Flask, render_template
from flask_bootstrap import Bootstrap
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField
from wtforms.validators import InputRequired, Email, Length
import pyodbc

conn = pyodbc.connect('DRIVER={PostgreSQL Unicode};SERVER=10.4.28.183;DATABASE=postgres;UID=postgres;PWD=developer2020')

app = Flask(__name__)
app.config['SECRET_KEY'] = 'mamamelamamamelavalaropa'
Bootstrap(app)

class LoginForm(FlaskForm):
    username = StringField('username', validators=[InputRequired(), Length(min=4, max = 80)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max = 80)])
    remember = BooleanField('remember me')


class RegisterForm(FlaskForm):
    email = StringField('email', validators=[InputRequired(), Email(message='Invalid email'), Length(max=50)])
    username = StringField('username', validators=[InputRequired(),Length(min=4, max = 80)])
    password = PasswordField('password', validators=[InputRequired(), Length(min=8, max = 80)])

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/login', methods=["GET", "POST"])
def login():
    form = LoginForm()

    if form.validate_on_submit():
        print( form.username.data + ' ' + form.password.data )

    return render_template('login.html', form = form)
    

@app.route('/register', methods=["GET", "POST"])
def signup():
    form = RegisterForm()

    if form.validate_on_submit():
        cnxn=conn.cursor()
        insert_user ='''INSERT INTO users( name,email,password, roleid, lastname, id, address,status) VALUES(?,?,?,?,?,?,?,?)'''
        cnxn.execute(insert_user, form.username.data, form.email.data, form.password.data, 1, '', '','',1)
        cnxn.commit()

        return '<h1>' + form.username.data + ' ' + form.email.data + ' welcome' + '</h1>'

    return render_template('signup.html', form = form)

@app.route('/dashboard')
def dashboard():
    return render_template('dashboard.html')

if __name__ == '__main__':
    app.run(debug=True, host='localhost', port = 3000)    
