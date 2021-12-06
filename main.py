from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, dirname, join


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Shelf(db.Model):
    __tablename__ = 'shelf'

    id = db.Column(db.String, primary_key=True)
    subject = db.Column(db.String)
    books = db.relationship('Book', back_populates='shelf')


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String, index=True)
    count = db.Column(db.Integer, default=1)
    shelf_id = db.Column(db.String, db.ForeignKey('shelf.id'))

    shelf = db.relationship('Shelf', back_populates='books')


@app.route('/')
def home():
    return render_template('home.html')


@app.route('/teacher_home')
def manage_books():
    return render_template('teacher/home.html')


@app.route('/add_books')
def add_books():
    return render_template('teacher/add_books.html')


@app.route('/student_home')
def student_home():
    return render_template('student/home.html')


@app.route('/borrow')
def borrow_get():
    return render_template('student/borrow.html')


@app.route('/search')
def book_search():
    return render_template('student/look_up.html')
