"""local server for Remote Pantry"""

from collections import OrderedDict
from datetime import datetime, timedelta

import bcrypt
from flask import Flask, render_template, redirect, request, flash, session, g, jsonify
from functools import wraps
from flask_debugtoolbar import DebugToolbarExtension
from jinja2 import StrictUndefined
import os

from pantry_functions import (login_required, get_user_by_uname, is_pword,
                              hash_it, basic_locs, get_locs, eatme_generator,
                              get_shop_lst, refilled, out_of_stock, to_refill,
                              make_pantry, make_new_user, better_than_boolean,
                              history_generator, add_to_pan, remove_from_shop,
                              get_tz)
from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db


app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secretSECRETsecret"
# Using an undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined

@app.route('/')
def log_in_form_display():
    """Homepage, log in or register, shows user info if logged in"""

    try:
        current_user = session["user_id"]
        current_user_obj = user = User.query.filter_by(user_id=current_user).first()
    except KeyError:
        current_user_obj = 0

    return render_template("homepage.html", user=current_user_obj)

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
    time_zone = int(request.form.get("time_zone"))

    # Transform and auto-create
    hashed_pword = hash_it(password)

    # Check if username has already been registered
    tricky_user = get_user_by_uname(username)

    if not tricky_user:
        # If username is not in system, allow registration
        make_new_user(username, hashed_pword, fname, lname, email, time_zone)
        flash("Successfully registered")

        # Set up session
        user = User.query.filter_by(username=username).first()
        session["user_id"] = user.user_id

        # Initialize 4 basic locations for a new user
        basic_locs(user.user_id)
        return redirect('/pantry')

    else:
        flash("There is already an account linked to this username.", 'danger')
        return redirect('/')

# @app.route('/add')
# @login_required
# def foodstuff_form_display():
#     """Display add form"""

#     current_user = session["user_id"]

#     # Pull and pass user's locations for radio buttons
#     user_locs = get_locs(current_user)

#     return render_template("add.html", user_locs=user_locs)

@app.route('/add_item', methods=["POST"])
@login_required
def add_foodstuff():
    """Add a new foodstuff"""

    # Grab from form
    is_pantry = better_than_boolean(request.form.get("pantry"))
    is_shopping = better_than_boolean(request.form.get("shop"))
    name = request.form.get("name")
    location = request.form.get("location")
    exp = request.form.get("exp")
    # Exp is optional, if left blank it comes in as empty string, needs convert
    if not exp:
        exp = None

    # Transform and auto-create
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
    return redirect('/pantry')

@app.route('/add_loc', methods=["POST"])
@login_required
def add_location():
    """Add a new location"""

    # Grab from form
    loc = request.form.get("loc")

    # Transform and auto-create
    current_user = session["user_id"]

    # Check if a location with this name already exists
    tricky_user = Location.query.filter_by(user_id=current_user, location_name=loc).first()

    if not tricky_user:
        # If location name is new, allow creation
        new_loc = Location(user_id=current_user, location_name=loc)
        db.session.add(new_loc)
        db.session.commit()
        flash("Successfully added")
        return redirect('/pantry')
    else:
        flash("Whoops! That location already exists in your pantry!", 'danger')
        return redirect('/pantry')

@app.route('/updatelocationformhandle', methods=["POST"])
@login_required
def update_location():
    """Change location_name"""

    # Grab from form
    new_name = request.form.get("new_name")
    location_id = request.form.get("loc_id")
    to_update = Location.query.filter_by(location_id=location_id).one()

    # Update location's name
    to_update.location_name = new_name
    db.session.commit()

    return jsonify({"locId": location_id, "newName": new_name})

@app.route('/pantry')
@login_required
def pantry_display():
    """Display pantry from database"""

    current_user = session['user_id']
    pantry = make_pantry(current_user)
    user_locs = get_locs(current_user)

    return render_template("pantry.html", pantry=pantry, user_locs=user_locs)

@app.route('/update', methods=["POST"])
@login_required
def update_foodstuff():
    """Update foodstuff item is_pantry and/or is_shopping in database"""

    # Grab from form
    empties = request.form.getlist("empty")
    refills = request.form.getlist("refill")

    out_of_stock(empties)
    to_refill(refills)

    return redirect('/pantry')

@app.route('/editpantryitem')
@login_required
def edit_item():
    """Display every field about a pantry item, with option to update any field"""

    pantry_id = request.args.get("pantry_id")

    # Grab from database
    item = Foodstuff.query.get(pantry_id)
    current_user = session['user_id']
    user_locs = get_locs(current_user)

    # Need to put user_locs into not-object form for jsonify
    loc_lst = [] # This will be a list of lists, inner list will be [id, name]
    for loc in user_locs:
        temp = []
        temp.append(loc.location_id)
        temp.append(loc.location_name)
        loc_lst.append(temp)


    """Convert to display format, get user's timezone, apply that to last_purch,
       which is saved in GMT in db, so user sees last_purch in their time zone"""
    tz = get_tz(current_user)
    ugly = (item.last_purch) + timedelta(hours=tz)
    pretty = ugly.strftime('%b %d, %Y')

    print "###################", item, item.is_shopping

    return jsonify({"pantryId": item.pantry_id, "userId": item.user_id,
                    "itemName": item.name, "isPantry": item.is_pantry,
                    "isShopping": item.is_shopping,
                    "lastPurch": pretty, "locationId": item.location_id,
                    "exp": item.exp, "description": item.description,
                    "barcodeId": item.barcode_id})

@app.route('/updatepantryitem', methods=["POST"])
@login_required
def update_single_foodstuff():
    """Update any field on a single foodstuff item"""

    # Grab from form
    pantry_id = request.form.get("pantry_id")
    is_shopping = better_than_boolean(request.form.get("shop"))
    is_pantry = request.form.get("pantry")
    name = request.form.get("name")
    last_purch = request.form.get("last_purch")
    location = request.form.get("location")
    exp = request.form.get("exp")
    description = request.form.get("description")

    #Transform and auto-create
    current_food_obj = Foodstuff.query.get(pantry_id)

    # Whatever fields a user has filled out will be updated
    # If no fields were filled, the item will not be changed
    change_counter = 0
    loc_change = False
    pantry_change = False
    exp_change = False
    name_change = False
    purch_change = False

    if name:
        print "flag name"
        name = name.encode("utf8")
        current_food_obj.name = name
        change_counter += 1
        name_change = name

    if location:
        location = int(location)
        if current_food_obj.location_id != location:
            current_food_obj.location_id = location
            change_counter += 1
            loc_change = True

    if exp:
        print "flag exp"
        exp = int(exp)
        current_food_obj.exp = exp
        change_counter += 1
        exp_change = True

    if description:
        print "flag description"
        description = description.encode("utf8")
        current_food_obj.description = description
        change_counter += 1

    if last_purch:
        print "flag purch"
        last_purch = datetime.strptime(last_purch, "%Y-%m-%d")
        # Have to add hours and minutes or date display isn't accurate
        proper_last_purch = last_purch.replace(hour=12, minute=00)
        """Getting timestamp on foodstuff was a problem. For now, just hardcoding 
           to noon since it will accurately represent the day, which is the only 
           thing I show to the user (and use to calc eat_me)."""
        current_food_obj.last_purch = proper_last_purch
        change_counter += 1
        purch_change = True

    if is_shopping:
        print "flag shopping"
        if current_food_obj.is_shopping != is_shopping:
            current_food_obj.is_shopping = is_shopping
            change_counter += 1

    if is_pantry:
        print "flag pan"
        is_pantry = better_than_boolean(is_pantry)
        if current_food_obj.is_pantry != is_pantry:
            current_food_obj.is_pantry = is_pantry
            change_counter += 1
            pantry_change = True

    print "change_counter", change_counter
    if change_counter != 0:
        db.session.add(current_food_obj)
        db.session.commit()
        flash("Your item has been updated")

    return jsonify({"locChange": loc_change, "nameChange": name_change,
                    "pantryId": pantry_id, "pantryChange": pantry_change,
                    "expChange": exp_change, "purchChange": purch_change})


@app.route('/shop')
@login_required
def store_form_display():
    """Display shopping list form"""

    # Grab all user's items with is_shopping status
    current_user = session["user_id"]
    shopping_list = get_shop_lst(current_user)
    user_locs = get_locs(current_user)


    return render_template("store.html", shopping_list=shopping_list, user_locs=user_locs)

@app.route('/restock', methods=["POST"])
@login_required
def restock_foodstuff():
    """Update foodstuff item"""

    # Grab from form
    refills = request.form.getlist("refill")
    exp = request.form.getlist("exp")
    pan_id = request.form.getlist("hidden_id")
    removals = request.form.getlist("delete")
    
    refilled(refills, exp, pan_id)
    remove_from_shop(removals)

    return redirect('/shop')

@app.route('/eatme')
@login_required
def eatme_display():
    """Display eatme"""

    # Grab all user's items with an exp
    current_user = session['user_id']
    eat_me = eatme_generator(current_user)
    user_locs = get_locs(current_user)

    return render_template("eatme.html", eat_me=eat_me, user_locs=user_locs)

@app.route('/map')
@login_required
def map_display():
    """Display google map, displays type 'supermarket' within 1000m, open now"""

    # Uses secrets.sh to get google map key
    # my_key = os.environ['GPLACES_KEY']
    # remember to run source secrets.sh in terminal before running this file!

    return render_template("map.html")

@app.route('/history')
@login_required
def history_display():
    """Display history page, user's empty items ordered by date"""

    # Grab all user's items marked pantry false
    current_user = session['user_id']
    history = history_generator(current_user)


    return render_template("history.html", history=history)

@app.route('/history_update', methods=["POST"])
@login_required
def history_update():
    """Update foodstuff item from history list"""

    # Grab from form
    empties = request.form.getlist("empty")
    refills = request.form.getlist("refill")

    add_to_pan(empties)
    to_refill(refills)

    return redirect('/history')

@app.route('/map_refresh')
@login_required
def reload_map():
    """Allows user to re-call googlimoops api"""
    return redirect('/map')


if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    # app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    #DebugToolbarExtension(app)

    """NORA, DONT YOU DARE FORGET TO SWITCH THIS BACK AND PUSH THIS VERSION TO
       GITHUB AND BREAK YOUR SERVER!!!!"""
    app.run()
    # app.run(port=5000, host='0.0.0.0')
