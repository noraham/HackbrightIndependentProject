"""local server for Remote Pantry"""

from datetime import datetime, timedelta
import bcrypt

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash, session, g)
from flask_debugtoolbar import DebugToolbarExtension
from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from collections import OrderedDict
from functools import wraps
from pantry_functions import (login_required, get_user_by_uname, is_pword,
                              hash_it, basic_locs, get_locs, eatme_generator,
                              get_shop_lst, refilled, out_of_stock, to_refill,
                              make_pantry, make_new_user)


app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secretSECRETsecret"
# Using an undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined

@app.route('/')
def log_in_form_display():
    """Homepage, log in or register"""

    return render_template("homepage.html")

@app.route('/login_handle', methods=["POST"])
def log_in_handle():
    """Log user into profile"""

    # Get form variables
    username = request.form["username"]
    pword_input = request.form["password"]

    # Check if username exists in db, redirect if doesn't exist
    user = get_user_by_uname(username)
    if not user:
        flash("No such user", 'danger')
        return redirect("/")

    # Transform and check if pword matches
    valid_password = is_pword(user, pword_input)

    # Log in or give incorrect pword flash
    if valid_password:
        session["user_id"] = user.user_id
        flash("Logged in")
        return redirect('/pantry')
    else:
        flash("Incorrect password", 'danger')
        return redirect("/")

@app.route('/logout')
@login_required
def logout():
    """Log out of site"""

    del session["user_id"]
    flash("Logged out")
    return redirect("/")

@app.route('/register_handle', methods=["POST"])
def newuser_form_handle():
    """Add new user to db"""

    # Grab from form
    username = request.form.get("username")
    password = request.form.get("password")
    fname = request.form.get("fname")
    lname = request.form.get("lname")
    email = request.form.get("email")

    # Transform and auto-create
    hashed_pword = hash_it(password)

    # check if username has already been registered
    tricky_user = get_user_by_uname(username)

    if not tricky_user:
        # If username is not in system, allow registration
        make_new_user(username, hashed_pword, fname, lname, email)
        flash("Successfully registered")

        # Set up session
        user = User.query.filter_by(username=username).first()
        session["user_id"] = user.user_id

        # Initialize 4 basic locations for a new user
        basic_locs(user.user_id)
        return redirect('/add')

    else:
        flash("There is already an account linked to this username.", 'danger')
        return redirect('/')

@app.route('/add')
@login_required
def foodstuff_form_display():
    """Display add form"""

    current_user = session["user_id"]

    # Pull and pass user's locations for radio buttons
    user_locs = get_locs(current_user)

    return render_template("add.html", user_locs=user_locs)

@app.route('/add_item', methods=["POST"])
@login_required
def add_foodstuff():
    """add a new foodstuff"""

    # Grab from form
    is_pantry = request.form.get("pantry")
    is_shopping = request.form.get("shop")
    name = request.form.get("name")
    location = request.form.get("location")
    exp = request.form.get("exp")
    # exp is optional, if left blank it comes in as empty string, needs convert
    if not exp:
        exp = None

    #Transform and auto-create
    if is_pantry == None:
        is_pantry = False
    if is_shopping == None:
        is_shopping = False
    current_user = session["user_id"]

    new_item = Foodstuff(user_id=current_user, name=name, is_pantry=is_pantry,
                         is_shopping=is_shopping, location_id=location, exp=exp)

    db.session.add(new_item)
    db.session.commit()

    flash("Successfully added")
    return redirect('/add')

@app.route('/add_loc', methods=["POST"])
@login_required
def add_location():
    """add a new location"""

    # Grab from form
    loc = request.form.get("loc")

    #Transform and auto-create
    current_user = session["user_id"]

    # Check if a location with this name already exists
    tricky_user = Location.query.filter_by(user_id=current_user, location_name=loc).first()

    if not tricky_user:
        # If location name is new, allow creation
        new_loc = Location(user_id=current_user, location_name=loc)
        db.session.add(new_loc)
        db.session.commit()
        flash("Successfully added")
        return redirect('/add')
    else:
        flash("Whoops! That location already exists in your pantry!", 'danger')
        return redirect('/add')

@app.route('/update/<int:location_id>')
@login_required
def update_location_form(location_id):
    """Display form to update location name"""

    loc = Location.query.filter_by(location_id=location_id).one()

    return render_template('edit_locs.html', loc=loc)

@app.route('/update_loc/<int:location_id>', methods=["POST"])
@login_required
def update_location(location_id):
    """change location_name"""

    # Grab from form
    new_name = request.form.get("new_name")
    to_update = Location.query.filter_by(location_id=location_id).one()

    # Update location's name
    to_update.location_name = new_name
    db.session.commit()

    return redirect("/pantry")

@app.route('/pantry')
@login_required
def pantry_display():
    """Display pantry from database"""

    current_user = session['user_id']
    pantry = make_pantry(current_user)

    return render_template("pantry.html", pantry=pantry)

@app.route('/update', methods=["POST"])
@login_required
def update_foodstuff():
    """update foodstuff item is_pantry and/or is_shopping in database"""

    # Grab from form
    empties = request.form.getlist("empty")
    refills = request.form.getlist("refill")

    out_of_stock(empties)
    to_refill(refills)

    return redirect('/pantry')

@app.route('/edit/<int:pantry_id>')
@login_required
def edit_item(pantry_id):
    """Display every field about a pantry item, with option to update any field"""

    # Grab from database
    item = Foodstuff.query.get(pantry_id)
    current_user = session['user_id']
    user_locs = get_locs(current_user)

    # Convert to display format, lazy fix for time zone problem, hardcoded to PST
    ugly = (item.last_purch) + timedelta(hours=-8)
    pretty = ugly.strftime('%b %d, %Y')

    return render_template("edit.html", item=item, lp=pretty, user_locs=user_locs)

@app.route('/update/<int:pantry_id>', methods=["POST"])
@login_required
def update_single_foodstuff(pantry_id):
    """update any field on a single foodstuff item"""

    # Grab from form
    is_pantry = request.form.get("pantry")
    is_shopping = request.form.get("shop")
    name = request.form.get("name")
    last_purch = request.form.get("last_purch")
    location = request.form.get("location")
    exp = request.form.get("exp")
    description = request.form.get("description")

    #Transform and auto-create
    current_food_obj = Foodstuff.query.get(pantry_id)

    # Whatever fields a user has filled out will be updated
    # If no fields were filled, the item will not be changed
    if name:
        name = name.encode("utf8")
        current_food_obj.name = name
    if location:
        location = int(location)
        current_food_obj.location_id = location
    if exp:
        exp = int(exp)
        current_food_obj.exp = exp
    if description:
        description = description.encode("utf8")
        current_food_obj.description = description
    if last_purch:
        last_purch = datetime.strptime(last_purch, "%Y-%m-%d")
        current_food_obj.last_purch = last_purch
    if is_pantry:
        current_food_obj.is_pantry = is_pantry
    if is_shopping:
        current_food_obj.is_shopping = is_shopping

    db.session.add(current_food_obj)
    db.session.commit()

    flash("Your item has been updated")
    return redirect('/pantry')


@app.route('/shop')
@login_required
def store_form_display():
    """Display shopping list form"""

    # Grab all user's items with is_shopping status
    current_user = session["user_id"]
    shopping_list = get_shop_lst(current_user)

    return render_template("store.html", shopping_list=shopping_list)

@app.route('/restock', methods=["POST"])
@login_required
def restock_foodstuff():
    """update foodstuff item"""

    # Grab from form
    refills = request.form.getlist("refill")
    exp = request.form.getlist("exp")
    pan_id = request.form.getlist("hidden_id")
    
    refilled(refills, exp, pan_id)

    return redirect('/shop')

@app.route('/eatme')
@login_required
def eatme_display():
    """Display eatme"""

    # Grab all user's items with an exp
    current_user = session['user_id']
    eat_me = eatme_generator(current_user)

    return render_template("eatme.html", eat_me=eat_me)

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
