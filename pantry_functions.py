"""functions for pantry server.py"""

from datetime import datetime, timedelta
import bcrypt

from jinja2 import StrictUndefined # can I cut this?
from flask import (Flask, render_template, redirect, request, flash, session, g)
from flask_debugtoolbar import DebugToolbarExtension
from tablesetup import User, Foodstuff, Location, Barcode, connect_to_db, db
from collections import OrderedDict
from functools import wraps

def login_required(f):
    """view decorator, wrap any functions where user must be logged in to view page.
       If not logged in, user is redirected home + flash message to log in"""
    
    @wraps(f)
    def decorated_function(*args, **kwargs):
        if session.get("user_id") is None:
            flash("Please log in or register.", 'danger')
            return redirect("/")
        return f(*args, **kwargs)
    return decorated_function


def get_user_by_uname(username):
    """takes username, returns user obj from database"""

    user = User.query.filter_by(username=username).first()
    return user

def is_pword(user, pword_input):
    """checks input pword against stored pword. Takes user obj and pword to 
    check, returns bool"""
    
    pword_in_table = user.pword.encode('utf8')
    valid_password = (bcrypt.hashpw(pword_input.encode('utf8'),
                      pword_in_table.encode('utf8')) == pword_in_table)
    return valid_password

def hash_it(pword):
    """takes a string, returns hashed string, uses bcrypt"""

    hashed_pword = bcrypt.hashpw(pword.encode('utf8'), bcrypt.gensalt(10))
    return hashed_pword

def basic_locs(user_id):
    """takes user id, creates 4 locations for this user in their pantry"""

    new_fridge = Location(user_id=user_id, location_name="Fridge")
    db.session.add(new_fridge)

    new_freezer = Location(user_id=user_id, location_name="Freezer")
    db.session.add(new_freezer)

    new_shelf = Location(user_id=user_id, location_name="Cupboard")
    db.session.add(new_shelf)

    new_rack = Location(user_id=user_id, location_name="Spice Rack")
    db.session.add(new_rack)

    db.session.commit()

def get_locs(user_id):
    """takes user id, returns list of user's location objects"""

    locs = Location.query.filter_by(user_id=user_id).order_by(Location.location_name).all()
    return locs

def eatme_generator(user_id):
    """takes user id, returns list of all items with expiry, sorted"""
    
    # Grab all user's foodstuffs with an exp
    with_exp = Foodstuff.query.filter(Foodstuff.user_id == user_id,
                                      Foodstuff.exp != None,
                                      Foodstuff.is_pantry == True).all()    
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
        # sort by time_left
        eat_me.sort(key=lambda x: x[3])

    return eat_me

def get_shop_lst(user_id):
    """takes user id, generates list of foodstuff objects that have been 
       placed on the shopping list"""

    shopping_list = Foodstuff.query.filter_by(user_id=user_id,
                                              is_shopping=True).all()
    return shopping_list

def refilled(refills, exp, pan_id):
    """Remove from shopping list, change pantry status, update last_purch
       keep exp if any, or update exp"""

    """Exp is optional, use what's in db if we have a value, else leave blank
       make a dictionary of id:exp values. caution: hidden value entry in this 
       dict is for all items on page, not just items user has toggled to refill.
       Therefore, go by refills list, use this dict to fill in exp"""
    exp_updates = {}
    for expi, pantry_id in zip(exp, pan_id):
        if not expi:
            foodie_obj = Foodstuff.query.filter_by(pantry_id=pantry_id).one()
            orig_expi = foodie_obj.exp
            expi = orig_expi
        exp_updates[pantry_id] = expi
    
    for item in refills:
        to_update = Foodstuff.query.get(item)
        to_update.is_pantry = True
        to_update.is_shopping = False
        to_update.last_purch = datetime.utcnow()
        to_update.exp = exp_updates[item]

    db.session.commit()

def out_of_stock(empties):
    """Update item's is_pantry value"""
    
    for item in empties:
        to_update = Foodstuff.query.get(item)
        to_update.is_pantry = False
    db.session.commit()

def to_refill(refills):
    """Update item's is_shopping value"""
    
    for item in refills:
        to_update = Foodstuff.query.get(item)
        to_update.is_shopping = True
    db.session.commit()

def make_pantry(user_id):
    """iterate through list of location objects, pulling all foodstuffs that
       match location id, append to pantry dictionary of
       location_name:[list of matching foodstuffs]"""
    
    user_locs = get_locs(user_id)
    pantry = OrderedDict()

    for loc in user_locs:
        # Make master list that we can add to, this will become the value
        items = []
        # Make a list of all foods objects in this location
        item_list = Foodstuff.query.filter_by(location_id=loc.location_id,
                    user_id=user_id, is_pantry=True).order_by(Foodstuff.name).all()

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
    return pantry

def make_new_user(uname, pword, fname, lname, email):
    """instantiate a User, add to db"""

    new_user = User(username=uname, pword=pword, fname=fname,
                        lname=lname, email=email)
    db.session.add(new_user)
    db.session.commit()

# Total = 13