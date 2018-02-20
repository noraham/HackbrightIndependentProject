from unittest import TestCase
# import doctest
from server import app
from tablesetup import connect_to_db, db
from seed import load_users, load_locations, load_items

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
        # fake a user_id in the session so we can get access to pages where this is required
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
        """runs after each test, deletes test data from database"""

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

        result = self.client.get("logout", follow_redirects=True)
        self.assertIn("Logged out", result.data)

# Run all tests if we run this file
if __name__ == "__main__":
    import unittest
    unittest.main()
