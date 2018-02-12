"""local server for Remote Pantry"""

from datetime import datetime, timedelta
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

    tricky_user = User.query.filter_by(email=email).first()

    if not tricky_user:
        new_user = User(email=email, pword=hashed_pword, fname=fname, lname=lname)
        db.session.add(new_user)
        db.session.commit()
        flash("Successfully registered")
        user = User.query.filter_by(email=email).first()
        session["user_id"] = user.user_id
        """Would like to initialize 3 basic locations for new users, giving me errors"""
        # new_fridge = Location(user_id=user, location_name="Fridge")
        # db.session.add(new_fridge)
        # new_freezer = Location(user_id=user, location_name="Freezer")
        # db.session.add(new_freezer)
        # new_shelf = Location(user_id=user, location_name="Shelf")
        # db.session.add(new_shelf)
        # db.session.commit()
        return redirect('/add')
    else:
        flash("There is already an account linked to this email. Please log in.")
        return redirect('/')

@app.route('/add')
def foodstuff_form_display():
    """Display add form"""

    current_user = session["user_id"]
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

    tricky_user = Location.query.filter_by(user_id=current_user, location_name=loc).first()

    if not tricky_user:
        new_loc = Location(user_id=current_user, location_name=loc)
        db.session.add(new_loc)
        db.session.commit()
        flash("Successfully added")
        return redirect('/add')
    else:
        flash("Whoops! That location already exists in your pantry!")
        return redirect('/add')

@app.route('/pantry')
def pantry_display():
    """Display pantry from database"""

    #generate a list of user's location objects
    current_user = session["user_id"]
    user_locs = Location.query.filter_by(user_id=current_user).all()

    """iterate through list of location objects, pulling all foodstuffs that match
    location id, append to dictionary of location_name:foodstuff"""
    pantry = {}
    for loc in user_locs:
        items = []
        item_list = Foodstuff.query.filter_by(location_id=loc.location_id,
                                         user_id=current_user, is_pantry=True).all()
        for each in item_list:
            temp = []
            temp.append(each.name)
            temp.append(each.pantry_id)
            items.append(temp)

        items.sort()
        pantry[loc.location_name] = items

    return render_template("pantry.html", pantry=pantry)

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

@app.route('/edit/<int:pantry_id>')
def edit_item(pantry_id):
    """Display edit form"""

    item = Foodstuff.query.get(pantry_id)
    ugly = item.last_purch
    pretty = ugly.strftime('%b %d, %Y')
    current_user = session["user_id"]
    user_locs = Location.query.filter_by(user_id=current_user).all()

    return render_template("edit.html", item=item, lp=pretty, user_locs=user_locs)

@app.route('/update/<int:pantry_id>', methods=["POST"])
def update_single_foodstuff(pantry_id):
    """update single foodstuff item in database"""
    print request.form
    # Grab from form
    is_pantry = request.form.get("pantry")
    is_shopping = request.form.get("shop")
    name = request.form.get("name")
    last_purch = request.form.get("last_purch")
    location = request.form.get("location")
    exp = request.form.get("exp")
    description = request.form.get("description")

    #Transform and auto-create
    # current_user = session["user_id"]
    current_food_obj = Foodstuff.query.get(pantry_id)

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
        if current_food_obj.is_pantry == True:
            current_food_obj.is_pantry = False
        else:
            current_food_obj.is_pantry = True
    if is_shopping:
        if current_food_obj.is_shopping == True:
            current_food_obj.is_shopping = False
        else:
            current_food_obj.is_shopping = True

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

    current_user = session["user_id"]
    shopping_list = Foodstuff.query.filter_by(user_id=current_user,
                                              is_shopping=True).all()

    return render_template("store.html", shopping_list=shopping_list)

@app.route('/restock', methods=["POST"])
def restock_foodstuff():
    """update foodstuff item is_pantry database"""

    refills = request.form.getlist("refill")

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

    # query foodstuffs for items with exp, order by ascending, pass to template.

    current_user = session["user_id"]
    eatme = Foodstuff.query.filter(Foodstuff.user_id == current_user,
                                              Foodstuff.exp != None).all()    
    eat_me = []
    for foodstuff in eatme:
        temp = []
        temp.append(foodstuff.pantry_id)
        temp.append(foodstuff.name)
        temp.append(foodstuff.location.location_name)
        last_purch = foodstuff.last_purch
        exp = foodstuff.exp
        exp_date = last_purch + timedelta(days=exp)
        time_left = exp_date - datetime.utcnow()
        temp.append(time_left)
        eat_me.append(temp)

    return render_template("eatme.html", eat_me=eat_me)

if __name__ == "__main__":
    # We have to set debug=True here, since it has to be True at the point
    # that we invoke the DebugToolbarExtension
    app.debug = True

    connect_to_db(app)

    # Use the DebugToolbar
    DebugToolbarExtension(app)

    app.run(host="0.0.0.0")
