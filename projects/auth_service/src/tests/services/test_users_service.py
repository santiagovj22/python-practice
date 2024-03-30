import unittest
from flask import Flask

from services.auth_service import init_service, register_user

app = Flask("test")
app.config['IS_TEST'] = True

class ServiceUsersTests(unittest.TestCase):
    def setUpd(self):
        '''TODO UNIT TEST HAHA'''
        init_service(app)

if __name__ == '__main__':
    unittest.main()
