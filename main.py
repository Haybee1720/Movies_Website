from flask import Flask, render_template, redirect, url_for, request
from flask_bootstrap import Bootstrap
from flask_sqlalchemy import SQLAlchemy
from flask_wtf import FlaskForm
import requests
from wtforms import BooleanField, StringField, validators, SubmitField, IntegerField, DecimalField
from wtforms.validators import InputRequired, Length

# create the extension
db = SQLAlchemy()

app = Flask(__name__)
app.config['SECRET_KEY'] = '8BYkEfBA6O6donzWlSihBXox7C0sKR6b'
Bootstrap(app)

# configure the SQLite database, relative to the app instance folder
app.config["SQLALCHEMY_DATABASE_URI"] = "sqlite:///movies-collection.db"

# initialize the app with the extension
db.init_app(app)


class Movies(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(250), unique=False, nullable=False)
    year = db.Column(db.String(250), nullable=False)
    description = db.Column(db.String(250), unique=False, nullable=False)
    rating = db.Column(db.String(250), nullable=False, unique=False)
    ranking = db.Column(db.Integer, nullable=False, unique=False)
    review = db.Column(db.String(250), unique=False, nullable=False)
    img_url = db.Column(db.String(250), unique=False, nullable=False)


@app.route("/")
def home():
    with app.app_context():
        db.create_all()
        movie_details = []
        movie_ranking = sorted([rank.ranking for rank in db.session.query(Movies).all()])
        print(movie_ranking)
        for movie_id in movie_ranking:
            arranged_movies = Movies.query.filter_by(ranking=movie_id).first()
            movie_details.append(arranged_movies)
    return render_template("index.html", movie_details=movie_details)


@app.route("/edit/<int:id>", methods=['GET', 'POST'])
def edit(id):
    url = f"https://api.themoviedb.org/3/movie/{id}"
    api_key = "8f248465d0f4db7c7717ce2c17bc9a65"
    response = requests.get(url, params={
        "api_key": api_key
    })
    movie = response.json()

    with app.app_context():
        class MyForm(FlaskForm):
            Review = StringField('Review', validators=[InputRequired()])
            Rating = DecimalField('Rating from 1 - 10',
                                  validators=[InputRequired(), validators.NumberRange(min=0, max=10)])
            submit = SubmitField("Submit")

        form = MyForm()
        if request.method == 'POST' and form.validate():
            # Checks if the entry is in the database,
            # if it is then it gets edited and if not it gets added to the dataase
            movie_to_edit = Movies.query.get(int(id))

            if movie_to_edit == None:
                backdrop_path = movie['backdrop_path']
                img_url = f"https://image.tmdb.org/t/p/original" + str(backdrop_path)
                with app.app_context():
                    db.create_all()
                    new_movie = Movies(title=movie['title'], img_url=img_url, year=str(movie['release_date']),
                                       description=movie['overview'], rating=str(form.Rating.data),
                                       review=str(form.Review.data), ranking=movie['vote_count'],
                                       id=movie['id'])
                    db.session.add(new_movie)
                    db.session.commit()
                    return redirect(url_for("home"))
            else:
                # Entry in database so it gets edited
                with app.app_context():
                    row_to_edit = Movies.query.get(int(id))
                    row_to_edit.rating = str(form.Rating.data)
                    row_to_edit.review = str(form.Review.data)
                    db.session.commit()
                    return redirect(url_for("home"))

    return render_template('edit.html', form=form, movie=movie)


@app.route("/delete/<int:id>")
def delete(id):
    movie_to_delete = Movies.query.get(id)
    db.session.delete(movie_to_delete)
    db.session.commit()
    return redirect(url_for("home"))


@app.route("/add", methods=["GET", "POST"])
def add():
    class SearchForm(FlaskForm):
        movie_title = StringField('Movie Title', validators=[InputRequired()])
        submit = SubmitField("Add Movie")

    form = SearchForm()
    if request.method == "POST" and form.validate():
        params = {
            "api_key": '8f248465d0f4db7c7717ce2c17bc9a65',
            "query": form.movie_title.data,
            "include_adult": False,
        }
        response = requests.get("https://api.themoviedb.org/3/search/movie", params=params)
        movie_list = response.json()["results"]

        return render_template("select.html", movie_list=movie_list)
    return render_template("add.html", form=form)


if __name__ == '__main__':
    app.run(debug=True)
