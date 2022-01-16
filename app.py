from random import choices
from flask import Flask, render_template, request, url_for, redirect, abort
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms.fields import SelectField, SubmitField
from os.path import abspath, dirname, join
from datetime import date


app = Flask(__name__)
BASE_DIR = abspath(dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = f'sqlite:///{join(BASE_DIR, "db.sqlite")}'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.config['SECRET_KEY'] = 'JAOSIUE8U903820ISKDJF'
db = SQLAlchemy(app)


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


class SubjectNotFound(BaseException):
    pass



class Subjects(db.Model):
    __tablename__ = 'subjects'

    subject = db.Column(db.String, primary_key=True)
    books = db.relationship('Book', backref='subject', uselist=True)


class Book(db.Model):
    __tablename__ = 'book'

    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(32), unique=True, index=True)
    book_subject = db.Column(db.String, db.ForeignKey('subjects.subject'))
    count = db.Column(db.Integer, default=1)
    borrowed = db.relationship('Borrows', backref='book', uselist=False)


class Borrows(db.Model):
    __tablename__ = 'borrows'

    id = db.Column(db.Integer, primary_key=True)
    borrower = db.Column(db.String(32), unique=True, index=True)
    borrower_class = db.Column(db.String(4))
    book_title = db.Column(db.String, db.ForeignKey('book.title'))
    librarian = db.Column(db.String)
    borrow_date = db.Column(db.Date, default=date.today())
    return_date = db.Column(db.Date)


def add_book(title: str, count=1, subject=None):
    title = ' '.join(title.split()).title()
    book_exists = Book.query.filter_by(title=title).first()

    if not book_exists:
        subject = Subjects.query.filter_by(subject=subject).first()

        if subject:
            book = Book(title=title, count=count, subject=subject)
        else:
            raise SubjectNotFound

        db.session.add(book)
        db.session.commit()
    else:
        raise BookExists


def borrow_book(book: str, name: str, return_date: date, student_class:str, librarian:str):
    book = ' '.join(book.split()).title()
    name = ' '.join(name.split()).title()
    librarian = ' '.join(librarian.split()).title()
    book = Book.query.filter_by(title=book).first()
    name_exists = bool(Borrows.query.filter_by(borrower=name).first())

    if book and book.count and not name_exists:
        borrow = Borrows(
            borrower=name,
            book=book,
            return_date=return_date,
            borrower_class=student_class,
            librarian=librarian,
        )

        book.count -= 1
        book.is_borrowed = True

        db.session.add_all([borrow, book])
        db.session.commit()

        return {'name_registered': borrow.borrower, 'borrow_id': borrow.id, 'book': borrow.book_title}
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
        book.is_borrowed = False
        db.session.add(book)
        db.session.delete(borrow)
        db.session.commit()


@app.route('/')
def home():
    obj = request.args
    return render_template('home.html', **obj)


@app.route('/add_book')
def add_book_get():
    return render_template('add_book.html')


@app.route('/add_book', methods=['POST'])
def add_book_post():
    title = request.form.get('title')
    count = int(request.form.get('count'))
    subject = request.form.get('subject').capitalize()
    print(subject)
    try:
        add_book(title, count, subject)
    except BookExists:
        return '<h1>That book is already added</h1>'
    except SubjectNotFound:
        subject_record = Subjects(subject=subject)
        db.session.add(subject_record)
        db.session.commit()
        add_book(title, count, subject)

    return redirect(url_for('home', added_book=True))


@app.route('/borrow/<title>')
def borrow_get(title=None):
    return render_template('borrow.html', title=title)


@app.route('/borrow', methods=['POST'])
def borrow_post():
    book = request.form.get('book')
    name = request.form.get('student_name')
    return_date = request.form.get('return_date')
    student_class = request.form.get('student_class')
    librarian = request.form.get('librarian')
    return_date = [int(i) for i in return_date.split('-')]
    return_date = date(*return_date)

    try:
        borrow_info = borrow_book(book, name, return_date, student_class, librarian)
        return redirect(url_for('home', **borrow_info))
    except OutOfBooks:
        return '<h1> Out of that book </h1>'
    except ReturnFirst:
        return '<h1> Return the book you last borrowed </h1>'



@app.route('/return')
def return_book_get():
    return render_template('return.html')


@app.route('/return', methods=['POST'])
def return_book_post():
    borrower = request.form.get('borrower')
    borrow_id = request.form.get('borrow_id')
    # book = request.form.get('book_title')

    try:
        if borrower:
            Return(student_name=borrower)
        elif borrow_id:
            borrow_id = int(borrow_id)
            Return(borrow_id=borrow_id)
    except BorrowNotFound:
        return '<h1>Wrong! You might have typo there.</h1>'
    else:
        return redirect(url_for('home'))


@app.route('/search')
def book_search():
    subject_query = request.args.get('subject')
    show_0 = request.args.get('only_available')
    subjects_list = Subjects.query.all()

    context = {
        'subjects': [subject.subject for subject in subjects_list],
        'results': None,
    }

    query = generate_query(show_0, subject_query)
    query_result = db.engine.execute(query).all()
    context['results'] = query_result

    return render_template('search.html', **context)


@app.route('/view_borrows')
def view_borrows():
    borrows = Borrows.query.all()
    return render_template('view_borowed.html', borrows=borrows)

def generate_query(show_0, subject_query):
    query = 'SELECT title, book_subject, count FROM book '

    if subject_query:
        query += f'WHERE book_subject = "{subject_query}" '
        if show_0:
            query += 'AND count > 0'
    elif show_0:
        query += 'WHERE count > 0'

    return query


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
