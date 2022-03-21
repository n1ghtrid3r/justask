import email
import unittest
import requests
import sqlite3

class ApiTest(unittest.TestCase):
    
    HOME_URL = "http://127.0.0.1:5000"
    REGISTER_URL = "http://127.0.0.1:5000/register"
    LOGIN_URL = "http://127.0.0.1:5000/login"
    PROFILE_URL= "http://127.0.0.1:5000/profile"


    connect = None
    cursor = None
    # SETUP_DATA_DICT = dict(email='email@gmail.com', first_name='John', last_name = 'Smith', username = 'JS0109', password = 'password123', role = 'Listener')
    SETUP_DATA = ['email@gmail.com', 'JS0109', 'John', 'Smith', 'password123', 'Listener']

    # test data:
    same_email = dict(email='email@gmail.com', first_name='value2', last_name = 'v', username = 'a', password = 'a', role = 'Speaker')
    
    
    # setup db with the setup data
    def setUp(self):
        self.connect = sqlite3.connect('justaskdatabase.db', check_same_thread=False)
        self.cursor = self.connect.cursor()
        self.cursor.execute("INSERT INTO users VALUES (?,?,?,?, ?, ?)", self.SETUP_DATA)
        self.connect.commit()

    # remove the setup data from db
    def tearDown(self):
        self.cursor.execute("DELETE FROM users WHERE email= ?", (self.SETUP_DATA[0],))
        self.cursor.execute("DELETE FROM users WHERE email= ?", (self.SETUP_DATA[0],))
        self.connect.commit()
        self.connect.close()
        


    def test_register_user_with_correct_details(self):
        # email should start of not being in db
        test_data = dict(email='value3', first_name='value2', last_name = 'v', username = 'a', password = 'a', role = 'Speaker')
        email_present = self.cursor.execute("SELECT * FROM users WHERE email= ?",(test_data["email"],)).fetchall()
        assert email_present == []
        
        # after post, user should be redirected, and data should be present in db
        r = requests.post(self.REGISTER_URL, data= test_data)
        email_present = self.cursor.execute("SELECT * FROM users WHERE email= ?",(test_data["email"],)).fetchall()
        assert r.url == ApiTest.LOGIN_URL
        assert email_present != []


    def test_access_home_page_unsigned_in(self):
        r = requests.get(ApiTest.HOME_URL)
        assert r.url == ApiTest.LOGIN_URL


    @unittest.skip
    def test_access_home_page_signed_in(self):
        r = requests.get(ApiTest.HOME_URL)
        assert r.url == ApiTest.PROFILE_URL

    # When home page accessed with GET request, if user logged in, 
    # go to profile page, else, go to the login page.
    def test_get_home_page(self):
        r = requests.get(ApiTest.HOME_URL)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.status_code, 200)
        self.assertEqual(r.status_code, 200)