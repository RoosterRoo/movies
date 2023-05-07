import os

from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField
from wtforms.validators import InputRequired
import requests
from dotenv import load_dotenv

load_dotenv()

app = Flask(__name__)
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///movies-collection.db'
app.config['SECRET_KEY'] = os.environ.get('SECRET_KEY')

API_KEY = os.environ.get('API_KEY')
MOVIE_DB_SEARCH_URL = "https://api.themoviedb.org/3/search/movie"
MOVIE_DB_DETAILS_URL = "https://api.themoviedb.org/3/movie"
MOVIE_DB_IMAGE_URL = "https://image.tmdb.org/t/p/w500"

Bootstrap(app)

db = SQLAlchemy(app)


class MoviesModel(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=True, nullable=False)
    year = db.Column(db.Integer, nullable=False)
    description = db.Column(db.String(250), nullable=False)
    rating = db.Column(db.Float, unique=True, nullable=True)
    ranking = db.Column(db.Integer, nullable=True)
    review = db.Column(db.String(250), nullable=True)
    img_url = db.Column(db.String(250), unique=True, nullable=False)

    def __str__(self):
        return f'<Book title: {self.title}>'


with app.app_context():
    db.create_all()


class EditForm(FlaskForm):
    rating = StringField('Edit Rating(out of 10)')
    review = StringField('Edit Description')
    submit = SubmitField('Save Changes')


class AddForm(FlaskForm):
    title = StringField('Movie Title', validators=[InputRequired()])
    submit = SubmitField('Add Movie')


@app.route("/")
def home():
    # new_movie = MoviesModel(title="Phone Booth", year=2002, description="Publicist Stuart Shepard finds himself\
    # trapped in a phone booth, pinned down by an extortionist's sniper rifle. Unable to leave or receive outside\
    # help, Stuart's negotiation with the caller leads to a jaw-dropping climax.", rating=7.3, ranking=10,
    #                         review="My favourite character was the caller.",
    #                         img_url="https://image.tmdb.org/t/p/w500/tjrX2oWRCM3Tvarz38zlZM7Uc10.jpg")
    # db.session.add(new_movie)
    # db.session.commit()
    all_movies = db.session.query(MoviesModel).order_by(MoviesModel.rating).all()
    for i in range(len(all_movies)):
        all_movies[i].ranking = len(all_movies) - i
    db.session.commit()
    return render_template("index.html", all_movies=all_movies)


@app.route('/find')
def find_movie():
    movie_id = request.args.get('id')
    response = requests.get(f'{MOVIE_DB_DETAILS_URL}/{movie_id}', params={'api_key': API_KEY})
    data = response.json()
    new_movie = MoviesModel(
        title=data['title'],
        year=data['release_date'].split('-')[0],
        img_url=f'{MOVIE_DB_IMAGE_URL}{data["poster_path"]}',
        description=data['overview']
    )
    db.session.add(new_movie)
    db.session.commit()
    return redirect(url_for('edit_rating', id=new_movie.id))


@app.route('/add', methods=['GET', 'POST'])
def add_movie():
    form = AddForm()
    if form.validate_on_submit():
        movie_title = form.title.data
        response = requests.get(url=MOVIE_DB_SEARCH_URL, params={'api_key': API_KEY, 'query': movie_title})
        options = response.json()['results']
        return render_template('select.html', options=options)

    return render_template('add.html', form=form)


@app.route('/edit', methods=['GET', 'POST'])
def edit_rating():
    form = EditForm()
    movie_id = request.args.get('id')
    movie = db.session.get(MoviesModel, movie_id)
    if form.validate_on_submit():
        if request.form.get('rating'):
            movie.rating = float(request.form.get('rating'))
        if request.form.get('review'):
            movie.review = request.form.get('review')
        db.session.commit()
        return redirect(url_for('home'))
    return render_template('edit.html', movie=movie, form=form)


@app.route('/delete', methods=['GET', 'POST'])
def delete_movie():
    movie_id = request.args.get('id')
    movie = db.session.get(MoviesModel, movie_id)
    db.session.delete(movie)
    db.session.commit()
    return redirect(url_for('home'))


if __name__ == '__main__':
    app.run(debug=True)
