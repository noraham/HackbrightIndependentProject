"""local server for Remote Pantry"""

from datetime import datetime, timedelta
import bcrypt

from jinja2 import StrictUndefined
from flask import (Flask, render_template, redirect, request, flash, session)
from flask_debugtoolbar import DebugToolbarExtension
from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from collections import OrderedDict


app = Flask(__name__)
app.config['DEBUG_TB_INTERCEPT_REDIRECTS'] = False

# Required to use Flask sessions and the debug toolbar
app.secret_key = "secretSECRETsecret"

# Using an undefined variable in Jinja2 raises an error
app.jinja_env.undefined = StrictUndefined


@app.route('/')
def Log_in_form_display():
    """Homepage, log in or register"""

    return render_template("homepage.html")

@app.route('/login_handle', methods=["POST"])
def log_in_handle():
    """Log user into profile"""

    # Get form variables
    email = request.form["email"]
    pword_input = request.form["password"]

    # Check if email exists in db
    user = User.query.filter_by(email=email).first()
    if not user:
        flash("No such user", 'danger')
        return redirect("/")

    # Transform and check
    pword_in_table = user.pword
    valid_password = (bcrypt.hashpw(pword_input.encode('utf8'),
                      pword_in_table.encode('utf8')) == pword_in_table)

    # Log in or give incorrect pword flash
    if valid_password:
        session["user_id"] = user.user_id
        flash("Logged in")
        return redirect('/pantry')
    else:
        flash("Incorrect password", 'danger')
        return redirect("/")

@app.route('/logout')
def logout():
    """Log out of site"""

    del session["user_id"]
    flash("Logged out")
    return redirect("/")

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

    # check if email has already been registered
    tricky_user = User.query.filter_by(email=email).first()

    if not tricky_user:
        # If email is not in system, allow registration
        new_user = User(email=email, pword=hashed_pword, fname=fname, lname=lname)
        db.session.add(new_user)
        db.session.commit()
        flash("Successfully registered")
        user = User.query.filter_by(email=email).first()
        session["user_id"] = user.user_id
        
        # Initialize these 3 basic locations for a new user
        new_fridge = Location(user_id=user.user_id, location_name="Fridge")
        db.session.add(new_fridge)
        new_freezer = Location(user_id=user.user_id, location_name="Freezer")
        db.session.add(new_freezer)
        new_shelf = Location(user_id=user.user_id, location_name="Shelf")
        db.session.add(new_shelf)
        db.session.commit()
        return redirect('/add')

    else:
        flash("There is already an account linked to this email. Please log in.", 'danger')
        return redirect('/')

@app.route('/add')
def foodstuff_form_display():
    """Display add form"""

    current_user = session["user_id"]
    # Pull and pass user's locations for radio buttons
    user_locs = Location.query.filter_by(user_id=current_user).all()

    return render_template("add.html", user_locs=user_locs)

@app.route('/add_item', methods=["POST"])
def add_foodstuff():
    """add a new foodstuff"""

    # Grab from form
    is_pantry = request.form.get("pantry")
    is_shopping = request.form.get("shop")
    name = request.form.get("name")
    location = request.form.get("location")
    exp = request.form.get("exp")

    #Transform and auto-create
    if is_pantry == None:
        is_pantry = False
    if is_shopping == None:
        is_shopping = False
    current_user = session["user_id"]
    location = int(location)

    # # For debug
    # print current_user, type(current_user)
    # print name, type(name)
    # print is_pantry, is_shopping
    # print location, type(location)
    # print exp, type(exp)

    """Expiration is optional, so adding items has 2 routes, depending if exp 
    has been declared"""
    if exp:
        exp = int(exp)
        new_item = Foodstuff(user_id=current_user, name=name, is_pantry=is_pantry,
                         is_shopping=is_shopping, location_id=location, exp=exp)
        db.session.add(new_item)
    else:
        exp = None
        new_item = Foodstuff(user_id=current_user, name=name, is_pantry=is_pantry,
                         is_shopping=is_shopping, location_id=location, exp=exp)
        db.session.add(new_item)
    
    db.session.commit()

    flash("Successfully added")
    return redirect('/add')

@app.route('/add_loc', methods=["POST"])
def add_location():
    """add a new location"""

    # Grab from form
    loc = request.form.get("loc")

    #Transform and auto-create
    current_user = session["user_id"]

    # For debug
    # print current_user, type(current_user)
    # print loc, type(loc)

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
def update_location_form(location_id):
    """Display form to update location name"""

    loc = Location.query.filter_by(location_id=location_id).one()

    return render_template('edit_locs.html', loc=loc)

@app.route('/update_loc/<int:location_id>', methods=["POST"])
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
def pantry_display():
    """Display pantry from database"""

    # Generate a list of user's location objects
    current_user = session["user_id"]
    user_locs = Location.query.filter_by(user_id=current_user).order_by(Location.location_name).all()

    """iterate through list of location objects, pulling all foodstuffs that 
    match location id, append to pantry dictionary of 
    location_name:[list of matching foodstuffs]"""
    pantry = OrderedDict()
    for loc in user_locs:

        # Make master list that we can add to, this will become the value
        items = []
        # Make a list of all foods objects in this location
        item_list = Foodstuff.query.filter_by(location_id=loc.location_id,
                    user_id=current_user, is_pantry=True).order_by(Foodstuff.name).all()

        """Make a list of a food object's name and id, append this list to the
        master list"""
        for each in item_list:
            temp = []
            temp.append(each.name)
            temp.append(each.pantry_id)
            items.append(temp)

        """Master list is now a list of lists, the internal lists have only the 
        foodstuff info our page needs, this master list becomes the value in 
        the pantry dictionary, where key is name of location."""
        pantry[loc] = items

    return render_template("pantry.html", pantry=pantry)

@app.route('/update', methods=["POST"])
def update_foodstuff():
    """update foodstuff item is_pantry and/or is_shopping in database"""

    # Grab from form
    empties = request.form.getlist("empty")
    refills = request.form.getlist("refill")

    # Update item's is_pantry value
    for item in empties:
        to_update = Foodstuff.query.get(item)
        to_update.is_pantry = False

    # Update item's is_shopping value
    for item in refills:
        to_update = Foodstuff.query.get(item)
        to_update.is_shopping = True

    db.session.commit()
    return redirect('/pantry')

@app.route('/edit/<int:pantry_id>')
def edit_item(pantry_id):
    """Display every field about a pantry item, with option to update any field"""

    # Grab from database   
    item = Foodstuff.query.get(pantry_id)
    current_user = session["user_id"]
    user_locs = Location.query.filter_by(user_id=current_user).all()
    
    # Convert to display format, lazy fix for time zone problem, hardcoded to PST
    ugly = (item.last_purch) + timedelta(hours=-8)
    pretty = ugly.strftime('%b %d, %Y')

    return render_template("edit.html", item=item, lp=pretty, user_locs=user_locs)

@app.route('/update/<int:pantry_id>', methods=["POST"])
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

    # # For debug
    # print "******************"
    # print pantry_id, type(pantry_id)
    # # print current_user, type(current_user)
    # print name, type(name)
    # print is_pantry, is_shopping
    # print location, type(location)
    # print exp, type(exp)
    # print last_purch, type(last_purch)
    # print description, type(description)
    # print "******************"
    
    db.session.commit()

    flash("Your item has been updated")
    return redirect('/pantry')


@app.route('/shop')
def store_form_display():
    """Display shopping list form"""

    # Grab all user's items with is_shopping status
    current_user = session["user_id"]
    shopping_list = Foodstuff.query.filter_by(user_id=current_user,
                                              is_shopping=True).all()

    return render_template("store.html", shopping_list=shopping_list)

@app.route('/restock', methods=["POST"])
def restock_foodstuff():
    """update foodstuff item"""

    # Grab from form
    refills = request.form.getlist("refill")

    # Remove from shopping list, change pantry status, update last_purch
    for item in refills:
        to_update = Foodstuff.query.get(item)
        to_update.is_pantry = True
        to_update.is_shopping = False
        to_update.last_purch = datetime.utcnow()

    db.session.commit()
    return redirect('/shop')

@app.route('/eatme')
def eatme_display():
    """Display eatme"""

    # Grab all user's items with an exp
    current_user = session["user_id"]
    with_exp = Foodstuff.query.filter(Foodstuff.user_id == current_user,
                                              Foodstuff.exp != None).all()    
    # Master list of lists, to be passed to template
    eat_me = []
    for foodstuff in with_exp:
        # Inner list that will be appended to master list
        temp = []
        temp.append(foodstuff.pantry_id)
        temp.append(foodstuff.name)
        temp.append(foodstuff.location.location_name)

        # DateTime math to display days until item expires
        last_purch = foodstuff.last_purch
        exp = foodstuff.exp
        # Lazy time zone fix: subtract 8 hours (hardcoded to PST)
        exp_date = last_purch + timedelta(days=exp, hours=-8)
        time_left = (exp_date - datetime.utcnow()).days
        temp.append(time_left)

        eat_me.append(temp)
        eat_me.sort(key=lambda x: x[3])

    return render_template("eatme.html", eat_me=eat_me)

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
