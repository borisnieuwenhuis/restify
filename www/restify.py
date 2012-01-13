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

    def get_body_dict(self, environ):
        length= int(environ.get('CONTENT_LENGTH', '0'))
        json_body = StringIO(environ['wsgi.input'].read(length)).getvalue()
        attrs = json.loads(json_body)
        #convert from unicode
        return dict((str(key), value) for key, value in attrs.iteritems())

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith("%s/%s" % (self.base_path, self.path)):
            log.info("request for %s" % (environ['PATH_INFO'], ))
            if environ['REQUEST_METHOD'] == 'POST':
                start_response('200 OK', [('Content-Type', 'application/json')])

                attrs = self.get_body_dict(environ)
                new_object = self.model_class(**attrs)
                new_object.put()

                return [json.dumps(to_dict(new_object))]
            elif environ['REQUEST_METHOD'] == 'GET':
                path = environ['PATH_INFO']
                path = path.split('/')
                if path[-1] == 'list':
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    model_list = self.model_class.all()
                    return [json.dumps([to_dict(object) for object in model_list])]
                else:
                    id = int(path[-1])
                    object = self.model_class.get_by_id(id)
                    if object:
                        start_response('200 OK', [('Content-Type', 'application/json')])
                        return [json.dumps(to_dict(object))]
                    else:
                        start_response('404 Not found', [('Content-Type', 'text/plain')])
            elif environ['REQUEST_METHOD'] == 'PUT':
                start_response('200 OK', [('Content-Type', 'application/json')])

                attrs = self.get_body_dict(environ)
                object = self.model_class.get_by_id(attrs['id'])
                if object:
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    for key, value in attrs.iteritems():
                        if key != 'id':
                            setattr(object, key, value)
                    object.put()
                    return [json.dumps(to_dict(object))]
                else:
                    start_response('404 Not found', [('Content-Type', 'text/plain')])

            elif environ['REQUEST_METHOD'] == 'DELETE':
                path = environ['PATH_INFO'].split('/')
                id = int(path[-1])
                object = self.model_class.get_by_id(id)
                if object:
                    start_response('200 OK', [('Content-Type', 'application/json')])
                    object.delete()
                else:
                    log.info("404")
                    start_response('404 Not found', [('Content-Type', 'text/plain')])
            else:
                start_response('405 Method Not Allowed', [('Content-Type', 'text/plain')])
            return ['']

        return self.app(environ, start_response)
