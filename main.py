from flask import Flask, render_template


app = Flask(__name__)


@app.route('/')
def index():
    return render_template('index.html')


@app.route('/manage')
def manage_books():
    return render_template('manage.html')


@app.route('/add_books')
def add_books():
    return render_template('add_books.html')


