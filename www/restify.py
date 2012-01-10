import logging
log = logging.getLogger(__name__)

from cStringIO import StringIO

try:
    import json
except ImportError:
    import simplejson as json

from google.appengine.ext import db

import datetime
import time

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def to_dict(model):
    output = {}

    for key, prop in model.properties().iteritems():
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, datetime.date):
            # Convert date/datetime to ms-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, db.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, db.Model):
            output[key] = to_dict(value)
        else:
            raise ValueError('cannot encode ' + repr(prop))

    output['id'] = model.key().id()
    return output

class RestifyMiddleware(object):

    def __init__(self, app, model_class, path):
        self.app = app
        self.model_class = model_class
        self.path = path
        self.base_path = "/restify"

    def __call__(self, environ, start_response):

        if environ['PATH_INFO'] == "%s/%s" % (self.base_path, self.path):
            log.info("request for %s" % (environ['PATH_INFO'], ))
            if environ['REQUEST_METHOD'] == 'POST':
                start_response('200 OK', [('Content-Type', 'application/json')])

                length= int(environ.get('CONTENT_LENGTH', '0'))
                json_body = StringIO(environ['wsgi.input'].read(length))
                attrs = json.loads(json_body.getvalue())
                attrs = dict((str(key), value) for key, value in attrs.iteritems())
                log.info(attrs)
                new_object = self.model_class(**attrs)
                new_object.put()

                return [json.dumps(to_dict(new_object))]
            else:
                start_response('404 Not found', [('Content-Type', 'text/plain')])


        return self.app(environ, start_response)
