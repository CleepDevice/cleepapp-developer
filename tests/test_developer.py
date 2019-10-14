import unittest
import logging
import sys
sys.path.append('../')
from backend.developer import Developer
from raspiot.utils import InvalidParameter, MissingParameter, CommandError, Unauthorized
from raspiot.libs.tests import session

LOG_LEVEL = logging.INFO

class TestDeveloper(unittest.TestCase):

    def setUp(self):
        self.session = session.TestSession(LOG_LEVEL)
        #next line instanciates your module, overwriting all useful stuff to isolate your module for tests
        self.module = self.session.setup(Developer)

    def tearDown(self):
        #clean session
        self.session.clean()

    #write your tests here defining functions
    #official documentation https://docs.python.org/2.7/library/unittest.html
    #...
    
