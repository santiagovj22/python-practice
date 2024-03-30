import unittest

from flask import Flask
app = Flask("test")

class ApiTests(unittest.TestCase):
    def setUp(self):
        '''THE SAME... PENDING TESTS'''
        app.config['IS_TEST'] = True
        app.testing = True
        self.app = app.test_client()

if __name__ == '__main__':
    unittest.main()
