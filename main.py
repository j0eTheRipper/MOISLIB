from flask import Flask, render_template
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, dirname, join


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Shelf(db.Model):
    __tablename__ = 'shelf'

    id = db.Column(db.Integer, primary_key=True)
    subject = db.Column(db.Integer, default=1)
    books = db.relationship('Book', backref='shelf')


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, index=True)
    shelf = db.Column(db.Integer, db.ForeignKey('shelf.id'))


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/teacher_home')
def manage_books():
    return render_template('teacher/home.html')


@app.route('/add_books')
def add_books():
    return render_template('teacher/add_books.html')


@app.route('/lend_books')
def lend_books():
    return render_template('teacher/lend.html')


@app.route('/student_home')
def student_home():
    return render_template('student/home.html')


