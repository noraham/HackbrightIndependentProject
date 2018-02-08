"""local server for Remote Pantry"""

import datetime
import bcrypt

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension
from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db


app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secretSECRETsecret"

# Using an undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def Log_in_form_display():
    """Homepage, log in"""

    return render_template("homepage.html")

@app.route('/login_handle', methods=["POST"])
def log_in_handle():
    """Log user into profile"""

    # Get form variables
    email = request.form["email"]
    pword_input = request.form["password"]

    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No such user")
        return redirect("/")

    # Transform and check
    pword_in_table = user.pword
    valid_password = (bcrypt.hashpw(pword_input.encode('utf8'), pword_in_table.encode('utf8'))
                     == pword_in_table)

    if valid_password:
        session["user_id"] = user.user_id
        flash("Logged in")
        return redirect('/pantry')

    else:
        flash("Incorrect password")
        return redirect("/")

@app.route('/logout')
def logout():
    """Log out of site"""

    del session["user_id"]
    flash("Logged out")
    return redirect("/")

@app.route('/register')
def newuser_form_display():
    """Register page"""

    return render_template("register.html")

@app.route('/register_handle', methods=["POST"])
def newuser_form_handle():
    """Add new user to db"""

    # Grab from form
    email = request.form.get("email")
    password = request.form.get("password")
    fname = request.form.get("fname")
    lname = request.form.get("lname")

    # Transform and auto-create
    password = password.encode('utf8')
    hashed_pword = bcrypt.hashpw(password, bcrypt.gensalt(10))
    now = datetime.datetime.now()

    new_user = User(email=email, pword=hashed_pword, fname=fname, lname=lname,
                    date_created=now)

    db.session.add(new_user)
    db.session.commit()

    flash("Successfully registered")
    return redirect('/add')

@app.route('/add')
def foodstuff_form_display():
    """Display add form"""

    return render_template("add.html")

@app.route('/pantry')
def pantry_display():
    """Display pantry from database"""

    # query foodstuffs by user_id and location_id, pass to template
    # Is there a non-hardcoded way to do this?
    current_user = session["user_id"]
    fridge = Foodstuff.query.filter_by(user_id=current_user, location_id=1,
                                       is_pantry=True).all()
    freezer = Foodstuff.query.filter_by(user_id=current_user, location_id=2,
                                        is_pantry=True).all()
    shelf = Foodstuff.query.filter_by(user_id=current_user, location_id=3,
                                      is_pantry=True).all()
    nope = Foodstuff.query.filter_by(user_id=current_user, location_id=4,
                                     is_pantry=True).all()

    return render_template("pantry.html", fridge=fridge, freezer=freezer,
                            shelf=shelf, nope=nope)

@app.route('/update', methods=["POST"])
def update_foodstuff():
    """update foodstuff item is_pantry and is_shopping in database"""

    empties = request.form.getlist("empty")

    for item in empties:
        to_update = Foodstuff.query.get(item)
        to_update.is_pantry = False

    refills = request.form.getlist("refill")

    for item in refills:
        to_update = Foodstuff.query.get(item)
        to_update.is_shopping = True

    db.session.commit()
    return redirect('/pantry')

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
