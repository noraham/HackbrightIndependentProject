from unittest import TestCase
# import doctest
from server import app, get_user_by_uname
from tablesetup import connect_to_db, db, Foodstuff, User, Location
from seed import load_users, load_locations, load_items
from pantry_functions import (login_required, get_user_by_uname, is_pword,
                              hash_it, basic_locs, get_locs, eatme_generator,
                              get_shop_lst, refilled, out_of_stock, to_refill,
                              make_pantry, make_new_user)

class UnitTests(TestCase):
    """Test the remote pantry functions from pantry_functions"""

    def setUp(self):
        """Runs before each test, gives testdb with fake_data"""
        
        # Connect to test database (must have 'createdb testdb' already!)
        connect_to_db(app, "postgresql:///testdb")

        # Create tables and add fake_data
        db.create_all()
        user_file = "fake_data/u.fake_users"
        loc_file = "fake_data/u.fake_locations"
        food_file = "fake_data/u.fake_foods"
        load_users(user_file)
        load_locations(loc_file)
        load_items(food_file)

    def tearDown(self):
        """Runs after each test, deletes test database"""

        db.session.remove()
        db.session.close()
        db.drop_all()

    def test_get_user_by_uname(self):
        """Takes username, returns user obj from database, this test returns
           True if it finds anything, false if it doesn't find."""

        # In this case, it should find the user object
        assert get_user_by_uname("test1") is not None
        # In this case, it should not find the user object
        assert get_user_by_uname("test") is None

    def test_is_pword(self):
        """This function checks input pword against stored pword"""

        fake_user = User.query.filter_by(user_id=1).one()
        # true positive (no false negatives)
        assert is_pword(fake_user, "secret1") is True
        # true negative (no false positives)
        assert is_pword(fake_user, "secret") is False

    def test_hash_it(self):
        """Uses bcrypt to hash a string"""

        # checks that bcrypt is connected
        assert hash_it("secret3")
    
    def test_basic_locs(self):
        """Auto-creates the 4 basic pantry locations for a new user
           caution: this is more os a SQL/db test"""

        # import pdb; pdb.set_trace()

        # Add new user to testdb, see if they have the locations
        test_user = User(username='anothertest', pword='verysecret', fname='first',
                         lname='last', email='abc@123.com')
        db.session.add(test_user)
        db.session.commit()

        user = User.query.filter_by(username='anothertest').first()
        test_id = user.user_id

        # true negative (no false positives)
        assert len(Location.query.filter_by(user_id=test_id).all()) == 0

        basic_locs(test_id) 

        # true positive (no false negatives)
        assert len(Location.query.filter_by(user_id=test_id).all()) == 4

    def test_get_locs(self):
        """Takes user id, returns list of user's location objects"""

        query = Location.query.filter_by(user_id=1).order_by(Location.location_name).all()
        function = get_locs(1)

        assert query == function

    def test_refilled(self):
        """Processes form from @store page: removes item from shopping list,
           change pantry status to true,
           update last purchase date
           update expiration"""

        # grab a foodstuff obj, get its attributes
        peppercorns = Foodstuff.query.get(3)
        milk = Foodstuff.query.get(1)
        eggs = Foodstuff.query.get(2)
        celery = Foodstuff.query.get(8)

        # check that refilled() updates is_pantry to True and is_shopping to False
        peppercorns.is_pantry = False
        peppercorns.is_shopping = True

        assert peppercorns.is_pantry != True
        assert peppercorns.is_shopping != False


        refilled([3], [''], [3])

        assert peppercorns.is_pantry == True
        assert peppercorns.is_shopping == False

        # check that refilled() uses exp in db if no exp is included in form
        peppercorns.exp = 10

        assert peppercorns.exp == 10

        refilled([3], [''], [3])

        assert peppercorns.exp == 10

        # check that refilled() updates exp in db
        peppercorns.exp = 10

        assert peppercorns.exp != 5

        refilled([3], ['5'], [3])

        assert peppercorns.exp == 5

        # check exp_updates dictionary correctly zips
        peppercorns.exp = 10
        milk.exp = 5
        eggs.exp = 4
        celery.exp = 3

        # refill all of them excpet celery, change exp of milk and eggs only
        refilled([3, 1, 2], ['', '20', '30', '40'], [3, 1, 2, 8])

        assert peppercorns.exp == 10
        assert milk.exp == 20
        assert eggs.exp == 30
        assert celery.exp != 40

class FlaskIntegrationTests(TestCase):
    """Integration tests for Remote Pantry
        Don't forget to start all function names with test!"""

    def setUp(self):
        """Runs before each test, gives fake server and testdb with fake_data"""
        # Creates fake server client that can make requests
        self.client = app.test_client()
        # This config will print all Flask errors to the console
        app.config['TESTING'] = True
        # To use session info, need secret key
        app.config['SECRET_KEY'] = 'wowsuchsecret'
        # Fake a user_id in the session so we can get access to pages where this is required
        with self.client.session_transaction() as sess:
            sess['user_id'] = 1
        
        # Connect to test database (must have 'createdb testdb' already!)
        connect_to_db(app, "postgresql:///testdb")

        # Create tables and add fake_data
        db.create_all()
        user_file = "fake_data/u.fake_users"
        loc_file = "fake_data/u.fake_locations"
        food_file = "fake_data/u.fake_foods"
        load_users(user_file)
        load_locations(loc_file)
        load_items(food_file)

    def tearDown(self):
        """Runs after each test, deletes test database"""

        db.session.remove()
        db.session.close()
        db.drop_all()

    def test_homepage(self):
        """Does the homepage display, is Flask working?"""

        result = self.client.get("/")
        self.assertIn("<h1>Hello, world!</h1>", result.data)
        self.assertIn("Login", result.data)

    def test_login(self):
        """Test that user can login and that the navbar changes to logout option"""

        login_info = {'username': "test1", 'password': "secret1"}

        result = self.client.post("/login_handle", data=login_info,
                                  follow_redirects=True)
        self.assertIn('Logout', result.data)
        self.assertIn('Add to Shopping List', result.data)

    def test_bad_uname_login(self):
        """Test that bad username correctly redirects, checks flash message"""

        login_info = {'username': "test", 'password': "secret1"}

        result = self.client.post("/login_handle", data=login_info,
                                  follow_redirects=True)
        self.assertIn("No such user", result.data)

    def test_bad_pword_login(self):
        """Test that bad password correctly redirects, checks flash message"""

        login_info = {'username': "test1", 'password': "secret"}

        result = self.client.post("/login_handle", data=login_info,
                                  follow_redirects=True)
        self.assertIn("Incorrect password", result.data)

    def test_register(self):
        """Test that new user can register, checks flash and redirect"""

        reg_info = {'username': "test4", 'password': "secret123",
                    'fname': 'test', 'lname': 'number 4',
                    'email': 'testeyemailio@gmail.com'}

        result = self.client.post("/register_handle", data=reg_info,
                                  follow_redirects=True)
        self.assertIn("Successfully registered", result.data)
        self.assertIn("<h3>Add a new item to the pantry:</h3>", result.data)

    def test_default_locations_register(self):
        """Test that a new user gets 4 default locations created upon registration"""

        reg_info = {'username': "test4", 'password': "secret123",
                    'fname': 'test', 'lname': 'number 4',
                    'email': 'testeyemailio@gmail.com'}

        result = self.client.post("/register_handle", data=reg_info,
                                  follow_redirects=True)
        self.assertIn("Fridge", result.data)
        self.assertIn("Freezer", result.data)
        self.assertIn("Cupboard", result.data)
        self.assertIn("Spice Rack", result.data)

    def test_bad_uname_register(self):
        """Test that new user can't register a uname already in use, checks flash"""

        reg_info = {'username': "test1", 'password': "secret123",
                    'fname': 'test', 'lname': 'number 4',
                    'email': 'testeyemailio@gmail.com'}

        result = self.client.post("/register_handle", data=reg_info,
                                  follow_redirects=True)
        self.assertIn("There is already an account linked to this username.", result.data)

    def test_logout(self):
        """Test that user can logout, checks flash"""

        result = self.client.get("/logout", follow_redirects=True)
        self.assertIn("Logged out", result.data)

    def test_add_foodstuff_noexp(self):
        """Test that user can add items to pantry and shopping, no exp
           Checks flash and redirect."""

        food_info = {'pantry': "True", 'shop': "True",
                    'name': 'test item no exp', 'location': '3', 'exp': ''}

        result = self.client.post("/add_item", data=food_info,
                                  follow_redirects=True)
        self.assertIn("Successfully added", result.data)
        self.assertIn("<h3>Add a new item to the pantry:</h3>", result.data)
        # assert user in db.session
                    

    def test_add_foodstuff_exp(self):
        """Test that user can add items to pantry and shopping, with exp
           (don't forget that exp and location come in as strings)"""

        food_info = {'pantry': "True", 'shop': "True",
                    'name': 'test item with exp', 'location': '3',
                    'exp': '10'}
 
        result = self.client.post("/add_item", data=food_info,
                                  follow_redirects=True)
        self.assertIn("Successfully added", result.data)
        self.assertIn("<h3>Add a new item to the pantry:</h3>", result.data)

    def test_add_foodstuff(self):
        """Test sqlalchemy db function: add and query"""

        food_test = Foodstuff(user_id=1, name='add test', is_pantry=True, is_shopping=False, location_id=1, exp=None)

        db.session.add(food_test)
        db.session.commit()

        self.assertTrue(Foodstuff.query.filter_by(name='add test').first() is not None)

    def test_no_dupe_locs(self):
        """Test that duplicate location name is rejected"""

        loc = {'loc': "Fridge"}

        result = self.client.post("/add_loc", data=loc,
                                  follow_redirects=True)
        self.assertIn("Whoops! That location already exists in your pantry!", result.data)

    def test_pantry_page_display(self):
        """Test that pantry page displays: table renders and all food items 
           from this user are being displayed"""

        result = self.client.get("/pantry")
        self.assertIn("<th>Out of Stock</th>", result.data)
        self.assertIn("milk", result.data)
        self.assertIn("eggs", result.data)
        self.assertIn("peppercorns", result.data)

    def test_edit_page_display(self):
        """Test that edit page renders"""

        item_info = {'pantry_id': 3}

        result = self.client.get("/edit/3", data=item_info, follow_redirects=True)
        self.assertIn("peppercorns", result.data)

    def test_loc_name_update(self):
        """Test that location name can be updated, checks redirect"""

        loc = {'new_name': "Frigidaire", 'location_id': 1}

        result = self.client.post("/update_loc/1", data=loc,
                                  follow_redirects=True)
        self.assertIn("<th>Out of Stock</th>", result.data)

    def test_store_page(self):
        """Move an item onto shopping list and check that it displays"""

        init_result = self.client.get("/shop", follow_redirects=True)
        self.assertNotIn("peppercorns", init_result.data) 

        foodobj_to_change = Foodstuff.query.filter_by(user_id=1,
                                              name='peppercorns').first()
        foodobj_to_change.is_shopping = True
        db.session.commit()

        result = self.client.get("/shop", follow_redirects=True)
        self.assertIn("peppercorns", result.data)        

    def test_refill(self):
        """Test that refill page renders and redirects"""

        refill = {'refill': 3, 'exp': '50', 'hidden_id': '3'}

        result = self.client.post("/restock", data=refill,
                                  follow_redirects=True)
        self.assertIn("Shopping List", result.data)

    def test_eatme(self):
        """Test that refill page renders and redirects"""

        result = self.client.get("/eatme", follow_redirects=True)
        self.assertIn("<p>Your foods, ordered by first to expire</p>", result.data)

    def test_update_single_foodstuff(self):
        """Update any field on a single foodstuff item"""

        # grab a sample food obj to test edits
        peppercorns = Foodstuff.query.get(3)

        assert peppercorns.is_pantry == True
        assert peppercorns.is_shopping == False
        assert peppercorns.name == 'peppercorns'
        assert peppercorns.location_id == 3
        assert peppercorns.exp == None
        assert peppercorns.description == None

        # pretend that we passed these values through form
        update = {'pantry': "False", 'shop': "True", 'name': 'peppie',
                  'location': '1', 'exp': '-25', 'description': 'this is my test item!'}

        result = self.client.post("/update/3", data=update,
                                  follow_redirects=True)
        # tests that form values correctly updated item in db
        peppercorns = Foodstuff.query.get(3)
        assert peppercorns.is_pantry == False
        assert peppercorns.is_shopping == True
        peppercorns = Foodstuff.query.get(3)
        assert peppercorns.name == 'peppie'
        assert peppercorns.location_id == 1
        assert peppercorns.exp == -25
        assert peppercorns.description != None
        # tests flash message
        self.assertIn("Your item has been updated", result.data)
        # tests redirect
        self.assertIn("<th>Add to Shopping List</th>", result.data)

# Run all tests if we run this file
if __name__ == "__main__":
    import unittest
    unittest.main()
