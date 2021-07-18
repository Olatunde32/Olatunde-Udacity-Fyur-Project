#----------------------------------------------------------------------------#
# Imports
#----------------------------------------------------------------------------#

import json
import dateutil.parser
import babel
from flask import Flask, render_template, request, Response, flash, redirect, url_for, abort
from flask_moment import Moment
from flask_sqlalchemy import SQLAlchemy
from flask_migrate import Migrate
import logging
from logging import Formatter, FileHandler, debug
from flask_wtf import Form
from forms import *
#----------------------------------------------------------------------------#
# App Config.
#----------------------------------------------------------------------------#

app = Flask(__name__)
moment = Moment(app)
app.config.from_object('config')

# connect to a local postgresql database
db = SQLAlchemy(app)
migrate = Migrate(app, db)
# db.create_all()

#----------------------------------------------------------------------------#
# Models.
#----------------------------------------------------------------------------#

# Venue model fields and relationship


class Venue(db.Model):
    __tablename__ = 'Venue'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    address = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    looking_for_talent = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='venue', lazy=True)

    # This method returns string representation of Venue object
    def __repr__(self):
        return f'<Venue {self.id} {self.name}>'


# Venue model fields and relationship

class Artist(db.Model):
    __tablename__ = 'Artist'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String)
    city = db.Column(db.String(120))
    state = db.Column(db.String(120))
    phone = db.Column(db.String(120))
    genres = db.Column(db.String(120))
    image_link = db.Column(db.String(500))
    facebook_link = db.Column(db.String(120))
    website = db.Column(db.String(120))
    looking_for_venue = db.Column(db.Boolean, default=False)
    seeking_description = db.Column(db.String(120))
    shows = db.relationship('Show', backref='artist', lazy=True)

    # This method returns string representation of Artist object
    def __repr__(self):
        return f'<Artist {self.id} {self.name}>'


class Show(db.Model):
    __tablename__ = 'show'

    id = db.Column(db.Integer, primary_key=True)
    artist_id = db.Column(db.Integer, db.ForeignKey(
        'artists.id'), nullable=False)
    venue_id = db.Column(db.Integer, db.ForeignKey(
        'venues.id'), nullable=False)
    start_time = db.Column(db.DateTime, default=datetime.now(), nullable=False)

    def __repr__(self):
        return f'<Show {self.id} {self.artist_id} {self.venue_id} {self.start_time}>'

#----------------------------------------------------------------------------#
# Filters.
#----------------------------------------------------------------------------#


def format_datetime(value, format='medium'):
    date = dateutil.parser.parse(value)
    if format == 'full':
        format = "EEEE MMMM, d, y 'at' h:mma"
    elif format == 'medium':
        format = "EE MM, dd, y h:mma"
    return babel.dates.format_datetime(date, format, locale='en')


app.jinja_env.filters['datetime'] = format_datetime

#----------------------------------------------------------------------------#
# Controllers.
#----------------------------------------------------------------------------#


@app.route('/')
def index():
    return render_template('pages/home.html')


#  Venues
#  ----------------------------------------------------------------

@app.route('/venues')
# Aggregated num_shows based on number of upcoming shows per venue.
def venues():

    # Querying dataset for cites and states of all venues
    areas = db.session.query(Venue.city, Venue.state).distinct(
        Venue.city, Venue.state)
    data = []
    for area in areas:

        # Querying venues and filter based on the area (city, venue)
        result = Venue.query.filter(Venue.state == area.state).filter(
            Venue.city == area.city).all()

        venue_data = []

        # Creating venues' response
        for venue in result:
            venue_data.append({
                'id': venue.id,
                'name': venue.name,
                'num_upcoming_shows': len(db.session.query(Show).filter(Show.start_time > datetime.now()).all())
            })

            data.append({
                'city': area.city,
                'state': area.state,
                'venues': venue_data
            })

    return render_template('pages/venues.html', areas=data)


@app.route('/venues/search', methods=['POST'])
def search_venues():

    # Search on artists with partial string search.
    # Case-insensitive
    search_term = request.form.get('search_term', '')
    result = db.session.query(Venue).filter(
        Venue.name.ilike(f'%{search_term}%')).all()
    count = len(result)
    response = {
        "count": count,
        "data": result
    }
    return render_template('pages/search_venues.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/venues/<int:venue_id>')
def show_venue(venue_id):
    # Shows the venue page with the given venue_id
    def show_venue(venue_id):
        venue = Venue.query.filter(Venue.id == venue_id).first()

        past = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
            Show.start_time < datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                    Artist.image_link, Show.start_time).all()

        upcoming = db.session.query(Show).filter(Show.venue_id == venue_id).filter(
            Show.start_time > datetime.now()).join(Artist, Show.artist_id == Artist.id).add_columns(Artist.id, Artist.name,
                                                                                                    Artist.image_link, Show.start_time).all()

        upcoming_shows = []

        past_shows = []

        for i in upcoming:
            upcoming_shows.append({
                'artist_id': i[1],
                'artist_name': i[2],
                'image_link': i[3],
                'start_time': str(i[4])
            })

        for i in past:
            past_shows.append({
                'artist_id': i[1],
                'artist_name': i[2],
                'image_link': i[3],
                'start_time': str(i[4])
            })

        if venue is None:
            abort(404)

        data = {
            "id": venue.id,
            "name": venue.name,
            "genres": [venue.genres],
            "address": venue.address,
            "city": venue.city,
            "state": venue.state,
            "phone": venue.phone,
            "website": venue.website,
            "facebook_link": venue.facebook_link,
            "looking_for_talent": venue.looking_for_talent,
            "seeking_description": venue.seeking_description,
            "image_link": venue.image_link,
            "past_shows": past_shows,
            "upcoming_shows": upcoming_shows,
            "past_shows_count": len(past),
            "upcoming_shows_count": len(upcoming),
        }
        return render_template('pages/show_venue.html', venue=data)

#  Create Venue
#  ----------------------------------------------------------------


@app.route('/venues/create', methods=['GET'])
def create_venue_form():
    form = VenueForm()
    return render_template('forms/new_venue.html', form=form)


@app.route('/venues/create', methods=['POST'])
def create_venue_submission():
    # Insert form data as a new Venue record in the db
    try:
        venue = Venue(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            address=request.form['address'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website=request.form['website'],
            looking_for_talent=json.loads(
                request.form['looking_for_talent'].lower()),
            seeking_description=request.form['seeking_description']
        )
        db.session.add(venue)
        db.session.commit()

        # On successful db insert, flash success
        flash('Venue ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        print(e)
        # On unsuccessful db insert, flash an error instead.
        flash('An error occurred. Venue ' +
              request.form['name'] + ' could not be listed')
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')


@app.route('/venues/<venue_id>', methods=['DELETE'])
def delete_venue(venue_id):
    # SQLAlchemy ORM to delete a record. Handle cases where the session commit could fail.

    # BONUS CHALLENGE: Implement a button to delete a Venue on a Venue Page, have it so that
    # clicking that button delete it from the db then redirect the user to the homepage
    try:
        Venue.query.filter(Venue.id == venue_id).delete()
        db.session.commit()
    except:
        db.session.rollback()
    finally:
        db.session.close()
    return render_template('pages/home.html')


#  Artists
#  ----------------------------------------------------------------


@app.route('/artists')
def artists():
    # Querying the database for artists
    data = Artist.query.all()
    return render_template('pages/artists.html', artists=data)


@app.route('/artists/search', methods=['POST'])
def search_artists():
    # Search on artists with partial string search. It is case-insensitive.
    search_term = request.form.get('search_term', '')
    result = db.session.query(Artist).filter(
        Artist.name.ilike(f'%{search_term}%')).all()
    count = len(result)
    response = {
        "count": count,
        "data": result
    }

    return render_template('pages/search_artists.html', results=response, search_term=request.form.get('search_term', ''))


@app.route('/artists/<int:artist_id>')
def show_artist(artist_id):
    # shows the artist page with the given artist_id
    artist = Artist.query.filter(Artist.id == artist_id).first()

    past = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time < datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                             Venue.image_link, Show.start_time).all()

    upcoming = db.session.query(Show).filter(Show.artist_id == artist_id).filter(
        Show.start_time > datetime.now()).join(Venue, Show.venue_id == Venue.id).add_columns(Venue.id, Venue.name,
                                                                                             Venue.image_link, Show.start_time).all()

    upcoming_shows = []

    past_shows = []

    for i in upcoming:
        upcoming_shows.append({
            'venue_id': i[1],
            'venue_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    for i in past:
        past_shows.append({
            'venue_id': i[1],
            'venue_name': i[2],
            'image_link': i[3],
            'start_time': str(i[4])
        })

    if artist is None:
        abort(404)

    data = {
        "id": artist.id,
        "name": artist.name,
        "genres": [artist.genres],
        "city": artist.city,
        "state": artist.state,
        "phone": artist.phone,
        "website": artist.website,
        "facebook_link": artist.facebook_link,
        "looking_for_venue": artist.looking_for_venue,
        "seeking_description": artist.seeking_description,
        "image_link": artist.image_link,
        "past_shows": past_shows,
        "upcoming_shows": upcoming_shows,
        "past_shows_count": len(past),
        "upcoming_shows_count": len(upcoming),
    }
    return render_template('pages/show_artist.html', artist=data)

#  Update
#  ----------------------------------------------------------------


@app.route('/artists/<int:artist_id>/edit', methods=['GET'])
# Populate form with fields from artist with ID <artist_id>
def edit_artist(artist_id):
    form = ArtistForm()
    artist = Artist.query.filter(Artist.id == artist_id).first()
    return render_template('forms/edit_artist.html', form=form, artist=artist)


@app.route('/artists/<int:artist_id>/edit', methods=['POST'])
def edit_artist_submission(artist_id):
    return redirect(url_for('show_artist', artist_id=artist_id))


@app.route('/venues/<int:venue_id>/edit', methods=['GET'])
def edit_venue(venue_id):
    form = VenueForm()
    venue = Venue.query.filter(Venue.id == venue_id).first()
    return render_template('forms/edit_venue.html', form=form, venue=venue)


@app.route('/venues/<int:venue_id>/edit', methods=['POST'])
# venue record with ID <venue_id> using the new attributes
def edit_venue_submission(venue_id):
    return redirect(url_for('show_venue', venue_id=venue_id))


#  Create Artist
#  ----------------------------------------------------------------


@app.route('/artists/create', methods=['GET'])
def create_artist_form():
    form = ArtistForm()
    return render_template('forms/new_artist.html', form=form)


@app.route('/artists/create', methods=['POST'])
def create_artist_submission():
    # called upon submitting the new artist listing form
    try:
        artist = Artist(
            name=request.form['name'],
            city=request.form['city'],
            state=request.form['state'],
            phone=request.form['phone'],
            genres=request.form.getlist('genres'),
            image_link=request.form['image_link'],
            facebook_link=request.form['facebook_link'],
            website=request.form['website'],
            looking_for_venue=json.loads(
                request.form['looking_for_venue'].lower()),
            seeking_description=request.form['seeking_description']
        )
        db.session.add(artist)
        db.session.commit()
        # on successful db insert, flash success
        flash('Artist ' + request.form['name'] + ' was successfully listed!')
    except Exception as e:
        print(e)
        # on unsuccessful db insert, flash an error instead.
        flash('An error occurred. Artist ' +
              request.form['name'] + ' could not be listed')
        db.session.rollback()
    finally:

        return render_template('pages/home.html')


#  Shows
#  ----------------------------------------------------------------

@app.route('/shows')
def shows():
    # displays list of shows at /shows
    # aggregated num_shows  based on number of upcoming shows per venue.
    data = Show.query.join(Artist, Artist.id == Show.artist_id).join(
        Venue, Venue.id == Show.venue_id).all()

    response = []
    for show in data:
        response.append({
            "venue_id": show.venue_id,
            "venue_name": show.venue.name,
            "artist_id": show.artist_id,
            "artist_name": show.artist.name,
            "artist_image_link": show.artist.image_link,
            "start_time": str(show.start_time)
        })
    return render_template('pages/shows.html', shows=response)


@app.route('/shows/create')
def create_shows():
    # renders form. do not touch.
    form = ShowForm()
    return render_template('forms/new_show.html', form=form)


@app.route('/shows/create', methods=['POST'])
def create_show_submission():
    # called to create new shows in the db, upon submitting new show listing form
    try:
        show = Show(
            artist_id=request.form['artist_id'],
            venue_id=request.form['venue_id'],
            start_time=request.form['start_time']
        )
        db.session.add(show)
        db.session.commit()
        flash('Show was successfully listed!')
    except Exception as e:
        print(e)
        flash('An error occurred. Show could not be listed')
        db.session.rollback()
    finally:
        db.session.close()

        return render_template('pages/home.html')


@app.errorhandler(404)
def not_found_error(error):
    return render_template('errors/404.html'), 404


@app.errorhandler(500)
def server_error(error):
    return render_template('errors/500.html'), 500


if not app.debug:
    file_handler = FileHandler('error.log')
    file_handler.setFormatter(
        Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
    )
    app.logger.setLevel(logging.INFO)
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)
    app.logger.info('errors')

#----------------------------------------------------------------------------#
# Launch.
#----------------------------------------------------------------------------#

# Default port:
if __name__ == '__main__':
    app.run()

# Or specify port manually:
'''
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))
    app.run(host='0.0.0.0', port=port)
'''
