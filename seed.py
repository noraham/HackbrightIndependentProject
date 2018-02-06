"""Utility file to seed fake data while building app"""

import datetime
from sqlalchemy import func

from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from server import app

def load_users(user_file):
    """Load users from u.fake_users into database."""

    print "Users"

    for row in open(user_file):
        row = row.rstrip()
        email, pword, fname, lname = row.split("|")
        timestamp = 

        user = User(email=email, pword=pword, fname=fname, lname=lname,
                    date_created=timestamp)

        # We need to add to the session or it won't ever be stored
        db.session.add(user)

    # Once we're done, we should commit our work
    db.session.commit()