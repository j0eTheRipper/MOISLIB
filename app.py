from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, dirname, join
from datetime import date


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), unique=True, index=True)
    count = db.Column(db.Integer, default=1)
    borrowed = db.relationship('Borrows', backref='book')


def add_book(title: str, count=1):
    title = ' '.join(title.split()).title()  # strips-off extra spaces
    book = Book(title=title, count=count)
    db.session.add(book)
    db.session.commit()


class Borrows(db.Model):
    __tablename__ = 'borrows'

    id = db.Column(db.Integer, primary_key=True)
    borrower = db.Column(db.String(32))
    book_title = db.Column(db.Integer, db.ForeignKey('book.title'))
    borrow_date = db.Column(db.Date)
    return_date = db.Column(db.Date)


def borrow_book(book, name, borrow_date, return_date):
    book = ' '.join(book.split()).title()
    book = Book.query.filter_by(title=book).first()
    name = ' '.join(name.split()).title()

    if book and book.count:
        Borrows.borrower = name
        Borrows.book_title = book
        Borrows.borrow_date = borrow_date
        Borrows.return_date = return_date
        book.count -= 1
        db.session.add_all([self, book])
        db.session.commit()
    elif not book:
        raise 'book not found.'
    elif not book.count:
        raise 'Out of Books!'


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
    user_query = request.args.get('search')

    context = {
        'book_title': '',
        'book_shelf': '',
    }

    if user_query:
        user_query = ' '.join(user_query.lower().split())
        result = Book.query.filter_by(title=user_query).first()
        if result:
            context['book_title'] = result.title
            context['book_shelf'] = result.shelf_id

    return render_template('student/look_up.html', **context)


@app.shell_context_processor
def imports():
    return dict(
        db=db,
        add_book=add_book,
        borrow_book=borrow_book,
        Book=Book,
        Borrows=Borrows
    )
