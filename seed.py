"""Utility file to seed fake data while building app"""

import datetime
from sqlalchemy import func

from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from server import app
import bcrypt


def load_users(user_file):
    """Load users from u.fake_users into database."""

    print "Users"

    for row in open(user_file):
        row = row.rstrip()
        email, pword, fname, lname = row.split("|")
        
        time = datetime.datetime.now()
        hashed_pword = bcrypt.hashpw(pword, bcrypt.gensalt(10))

        # validPassword = bcrypt.hashpw(pword_input, pword_in_table.encode('utf8')) == pword_in_table

        user = User(email=email, pword=hashed_pword, fname=fname, lname=lname,
                    date_created=time)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()

def load_locations(loc_file):
    """Load locations from u.fake_locations into database."""

    print "Locations"

    for row in open(loc_file):
        loc_nam = row.rstrip()

        loc = Location(location_name=loc_nam)

        db.session.add(loc)

    db.session.commit()

def load_items(food_file):
    """Load items from u.fake_foods into database."""

    print "Foodstuffs"

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

"""I don't think I need to use this since I'm not passing my user_id..."""
# def set_val_user_id():
#     """Set value for the next user_id after seeding database"""

#     # Get the Max user_id in the database
#     result = db.session.query(func.max(User.user_id)).one()
#     max_id = int(result[0])

#     # Set the value for the next user_id to be max_id + 1
#     query = "SELECT setval('users_user_id_seq', :new_id)"
#     db.session.execute(query, {'new_id': max_id + 1})
#     db.session.commit()

if __name__ == "__main__":
    connect_to_db(app)
    db.create_all()

    user_file = "fake_data/u.fake_users"
    loc_file = "fake_data/u.fake_locations"
    food_file = "fake_data/u.fake_foods"
    load_users(user_file)
    load_locations(loc_file)
    load_items(food_file)
    #set_val_user_id()
