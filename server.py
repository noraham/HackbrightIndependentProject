"""local server for Remote Pantry"""

from jinja2 import StrictUndefined

from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension

from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db


app = Flask(__name__)

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secretSECRETsecret"

# Normally, if you use an undefined variable in Jinja2, it fails silently.
# This is horrible. Fix this so that, instead, it raises an error.
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def Log_in_form_display():
    """Homepage, log in"""

    return render_template("homepage.html")

@app.route('/register')
def newuser_form_display():
    """Register page"""

    return render_template("register.html")

@app.route('/add')
def foodstuff_form_display():
    """Display add form"""

    return render_template("add.html")

@app.route('/pantry')
def pantry_display():
    """Display pantry from database"""

    # query foodstuffs by user_id and location_id, pass to template

    return render_template("pantry.html")

@app.route('/edit')
def edit_item():
    """Display edit form"""

    # need to add variable to route address

    return render_template("edit.html")

@app.route('/shop')
def store_form_display():
    """Display shopping list form"""

    # query foodstuffs by is_shopping=True, pass to template

    return render_template("store.html")

@app.route('/eatme')
def eatme_display():
    """Display eatme"""

    # query foodstuffs for items with exp, order by ascending, pass to template.

    return render_template("eatme.html")

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
