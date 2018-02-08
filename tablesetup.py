"""Models and database functions for Remote Pantry"""

from flask_sqlalchemy import SQLAlchemy
import bcrypt
from datetime import datetime
# Connection to PosgreSQL database
db = SQLAlchemy()

###############################################################################
"""Model classes, for object-oriented relational db"""

class User(db.Model):
    """User of pantry site"""

    __tablename__ = "users"

    user_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    email = db.Column(db.String(50), nullable=False, unique=True)
    pword = db.Column(db.String(150), nullable=False)
    fname = db.Column(db.String(50), nullable=False)
    lname = db.Column(db.String(50), nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    is_active = db.Column(db.Boolean, default=True, nullable=False)

    def __repr__(self):
        """display user objects nicely, for debugging"""
        return "<User id={} email={} name={} {}>".format(self.user_id,
                                            self.email, self.fname, self.lname)

class Foodstuff(db.Model):
    """Pantry item of pantry site"""

    __tablename__ = "foodstuffs"

    pantry_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'))
    name = db.Column(db.String(50), nullable=False)
    is_shopping = db.Column(db.Boolean, default=False, nullable=False)
    is_pantry = db.Column(db.Boolean, default=True, nullable=False)
    last_purch = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    first_add = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    location_id = db.Column(db.Integer, db.ForeignKey('locations.location_id'))
    exp = db.Column(db.Integer, nullable=True)
    description = db.Column(db.String(300), nullable=True)
    barcode_id = db.Column(db.Integer, db.ForeignKey('barcodes.barcode_id'),
                           nullable=True)

    user = db.relationship('User', backref=db.backref("foodstuffs"))
    location = db.relationship('Location', backref=db.backref("locations"))
    barcode = db.relationship('Barcode', backref=db.backref("barcodes"))

    def __repr__(self):
        """display food objects nicely, for debugging"""
        return "<Food id={} name={}>".format(self.pantry_id, self.name)

class Location(db.Model):
    """Location table for pantry site"""

    __tablename__ = "locations"

    location_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    location_name = db.Column(db.String(50), nullable=False)

    def __repr__(self):
        """display locations nicely, for debugging"""
        return "<Location id={} name={}>".format(self.location_id,
                                                 self.location_name)

class Barcode(db.Model):
    """Barcode table for pantry site"""

    __tablename__ = "barcodes"

    barcode_id = db.Column(db.Integer, autoincrement=True, primary_key=True)
    food_type = db.Column(db.String(50), nullable=True)

    def __repr__(self):
        """display locations nicely, for debugging"""
        return "<barcode id={}>".format(self.barcode_id)

###############################################################################
"""Helper functions"""

def connect_to_db(app):
    """Connect the database to Flask"""

    # Configure to use PostgreSQL database
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql:///pantry'
    app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
    app.config['SQLALCHEMY_ECHO'] = True
    db.app = app
    db.init_app(app)


if __name__ == "__main__":
    # As a convenience, if we run this module interactively, it will leave
    # you in a state of being able to work with the database directly.

    from server import app

    connect_to_db(app)
    print "Connected to DB."
