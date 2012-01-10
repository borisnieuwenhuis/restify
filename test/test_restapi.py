import sys
import unittest
import os
import urllib
try:
    import json
except ImportError:
    import simplejson as json

from webtest import TestApp

#use NoseGAE to run tests
#sudo easy_install Nose
#sudo easy_install NoseGAE
#run test:
#nosetests -vv --with-gae --gae-lib-root=/home/henk/opt/google_appengine --gae-application=www --where test

import logging
logging.basicConfig(level = logging.INFO)

log = logging.getLogger(__name__)

#this will allow us to import main.py from the webapp
www_root = os.path.abspath(os.path.join(os.path.dirname(__file__), '../www'))
sys.path.insert(0, www_root)

from main import get_application
from restify import *
from member import Member

class RestApiTestCase(unittest.TestCase):

    def setUp(self):

        #clears existing data
        from google.appengine.ext import db
        from google.appengine.ext import testbed
        from google.appengine.api import apiproxy_stub_map

        # First, create an instance of the Testbed class.
        self.testbed = testbed.Testbed()
        # Then activate the testbed, which prepares the service stubs for use.
        self.testbed.activate()
        # Next, declare which service stubs you want to use.
        self.testbed.init_datastore_v3_stub()

        self.testbed.init_taskqueue_stub(root_path = www_root)
        self.testbed.init_memcache_stub()

        self.app = RestifyMiddleware(get_application(), Member, 'member')
        self.app = TestApp(self.app, extra_environ = dict(HTTP_HOST='localhost:8080'))

    def tearDown(self):
        self.testbed.deactivate()

    def test_restify(self):

        member = {'name': 'boris'}
        result = self.app.post("/restify/member", json.dumps(member))
        result = result.json
        self.assertTrue(result.has_key('id'))

def main():
    unittest.main()

