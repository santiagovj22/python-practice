import unittest
from flask import Flask

from persistence.db import init_db
from persistence.users_dao import user_exists, create_user

app = Flask("test")
app.config['IS_TEST'] = True

class PersistenceUsersTests(unittest.TestCase):
    def setUp(self):
        '''AGAIN PENDING UNITEST HAHA'''
        init_db(app)

if __name__ == '__main__':
    unittest.main()
