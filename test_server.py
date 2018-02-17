from unittest import TestCase
# import doctest
from server import app
from tablesetup import connect_to_db, db
from seed import load_users, load_locations, load_items

class IntegrationTests(TestCase):
    """Integration tests for Remote Pantry"""

    def setUp(self):
        self.client = app.test_client()
        # Creates fake server client that can make requests
        app.config['TESTING'] = True
        # This config will print all Flask errors to the console

        # Connect to test database
        connect_to_db(app, "postgresql:///testdb")

        # Create tables and add sample data
        db.create_all()
        user_file = "fake_data/u.fake_users"
        loc_file = "fake_data/u.fake_locations"
        food_file = "fake_data/u.fake_foods"
        load_users(user_file)
        load_locations(loc_file)
        load_items(food_file)

    def tearDown(self):
        """runs after each test, deletes test data from database"""

        db.session.close()
        db.drop_all()

    def test_homepage(self):
        """Does the homepage display, is Flask working?"""

        result = self.client.get("/")
        self.assertIn("<h1>Hello, world!</h1>", result.data)
        self.assertIn("Login", result.data)

    def test_login(self):
        """Test that user can login and that the navbar changes to display logout option"""

        login_info = {'username': "test1", 'password': "secret1"}

        result = self.client.post("/login_handle", data=login_info, follow_redirects=True)
        self.assertIn('Logout', result.data)
        self.assertIn('Add to Shopping List', result.data)

# Run all tests if we run this file
if __name__ == "__main__":
    import unittest
    unittest.main()
