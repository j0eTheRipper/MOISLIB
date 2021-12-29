from flask import Flask, render_template, request, url_for, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
from os.path import abspath, dirname, join
from datetime import date


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'JAOSIUE8U903820ISKDJF'
db = SQLAlchemy(app)
migrate = Migrate(app, db)


class BookExists(BaseException):
    pass


class BookNotFound(BaseException):
    pass


class OutOfBooks(BaseException):
    pass


class BorrowNotFound(BaseException):
    pass


class ReturnFirst(BaseException):
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
    borrower = db.Column(db.String(32), unique=True, index=True)
    book_title = db.Column(db.Integer, db.ForeignKey('book.title'))
    borrow_date = db.Column(db.Date, default=date.today())
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


def borrow_book(book: str, name: str, return_date: date, borrow_date: date = date.today()):
    book = ' '.join(book.split()).title()
    name = ' '.join(name.split()).title()
    book = Book.query.filter_by(title=book).first()
    name_exists = bool(Borrows.query.filter_by(borrower=name).first())

    if book and book.count and not name_exists:
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
    elif name_exists:
        raise ReturnFirst


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


@app.route('/add_book')
def add_book_get():
    return render_template('add_book.html')


@app.route('/add_book', methods=['POST'])
def add_book_post():
    title = request.form.get('title')
    count = int(request.form.get('count'))
    try:
        add_book(title, count)
    except BookExists:
        abort(406)
    return redirect(url_for('home'))


@app.route('/borrow')
def borrow_get():
    return render_template('borrow.html')


@app.route('/borrow', methods=['POST'])
def borrow_post():
    book = request.form.get('book')
    name = request.form.get('student_name')
    return_date = request.form.get('return_date')
    return_date = [int(i) for i in return_date.split('-')]
    return_date = date(*return_date)

    try:
        borrow_book(book, name, return_date)
    except OutOfBooks:
        return '<h1> Out of that book </h1>'
    except ReturnFirst:
        return '<h1> Return the book you last borrowed </h1>'

    return redirect(url_for('home'))


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

    return render_template('search.html', **context)


@app.errorhandler(406)
def handle_406(err):
    return render_template('book_exists.html'), 406


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
