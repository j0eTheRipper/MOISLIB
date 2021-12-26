from flask import Flask, render_template, request
from flask_sqlalchemy import SQLAlchemy
from os.path import abspath, dirname, join
from datetime import date


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
db = SQLAlchemy(app)


class BookExists(BaseException):
    pass


class BookNotFound(BaseException):
    pass


class OutOfBooks(BaseException):
    pass


class BorrowNotFound(BaseException):
    pass


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), unique=True, index=True)
    count = db.Column(db.Integer, default=1)
    borrowed = db.relationship('Borrows', backref='book')


class Borrows(db.Model):
    __tablename__ = 'borrows'

    id = db.Column(db.Integer, primary_key=True)
    borrower = db.Column(db.String(32))
    book_title = db.Column(db.Integer, db.ForeignKey('book.title'))
    borrow_date = db.Column(db.Date)
    return_date = db.Column(db.Date)


def add_book(title: str, count=1):
    title = ' '.join(title.split()).title()
    book_exists = Book.query.filter_by(title=title).first()

    if not book_exists:
        book = Book(title=title, count=count)

        db.session.add(book)
        db.session.commit()
    else:
        raise BookExists


def borrow_book(book: str, name: str, borrow_date: date, return_date: date):
    book = ' '.join(book.split()).title()
    name = ' '.join(name.split()).title()
    book = Book.query.filter_by(title=book).first()

    if book and book.count:
        borrow = Borrows(
            borrower=name,
            book=book,
            borrow_date=borrow_date,
            return_date=return_date,
        )

        book.count -= 1

        db.session.add_all([borrow, book])
        db.session.commit()
    elif not book:
        raise BookNotFound
    elif not book.count:
        raise OutOfBooks


class Return:
    def __init__(self, borrow_id: int = 0, student_name: str = ''):
        self.student_name = ' '.join(student_name.split()).title() if student_name else ''
        self.borrow_id = borrow_id

        self.return_book()

    def return_book(self):
        if self.borrow_id:
            self.return_by_id()
        elif self.student_name:
            self.return_by_student_name()

    def return_by_student_name(self):
        borrow = Borrows.query.filter_by(borrower=self.student_name).first()
        if borrow:
            self.return_(borrow)
        else:
            raise BorrowNotFound

    def return_by_id(self):
        borrow = Borrows.query.filter_by(id=self.borrow_id).first()

        if borrow:
            self.return_(borrow)
        else:
            raise BorrowNotFound

    @staticmethod
    def return_(borrow):
        book = borrow.book
        book.count += 1
        db.session.add(book)
        db.session.delete(borrow)
        db.session.commit()


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
        Borrows=Borrows,
        Return=Return,
    )
