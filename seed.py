"""Utility file to seed fake data while building app"""

import datetime
from sqlalchemy import func

from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from server import app
import bcrypt


def load_users(user_file):
    """Load users from u.fake_users into database."""

    for row in open(user_file):
        row = row.rstrip()
        username, pword, fname, lname, email = row.split("|")
        
        time = datetime.datetime.now()
        hashed_pword = bcrypt.hashpw(pword, bcrypt.gensalt(10))

        user = User(username=username, pword=hashed_pword, fname=fname, lname=lname,
                    date_created=time, email=email)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()

def load_locations(loc_file):
    """Load locations from u.fake_locations into database."""

    for row in open(loc_file):
        row = row.rstrip()
        user_id, name = row.split("|")

        user_id = int(user_id)

        loc = Location(location_name=name, user_id=user_id)

        db.session.add(loc)

    db.session.commit()

def load_items(food_file):
    """Load items from u.fake_foods into database."""

    for row in open(food_file):
        row = row.rstrip()
        user, name, loc = row.split("|")
        user = int(user)
        loc = int(loc)
        now = datetime.datetime.now()

        item = Foodstuff(user_id=user, name=name, location_id=loc,
                         last_purch=now, first_add=now)

        db.session.add(item)

    db.session.commit()

if __name__ == "__main__":
    connect_to_db(app)
    db.create_all()

    user_file = "fake_data/u.fake_users"
    loc_file = "fake_data/u.fake_locations"
    food_file = "fake_data/u.fake_foods"
    load_users(user_file)
    load_locations(loc_file)
    load_items(food_file)
