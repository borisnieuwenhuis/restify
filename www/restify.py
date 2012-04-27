import logging
log = logging.getLogger(__name__)

from cStringIO import StringIO

try:
    import json
except ImportError:
    import simplejson as json

from google.appengine.ext import db
from datetime import datetime, date
import time, urlparse

SIMPLE_TYPES = (int, long, float, bool, dict, basestring, list)

def to_dict(model):
    output = {}

    for key, prop in model.properties().iteritems():
        value = getattr(model, key)

        if value is None or isinstance(value, SIMPLE_TYPES):
            output[key] = value
        elif isinstance(value, date):
            # Convert date/datetime to s-since-epoch ("new Date()").
            ms = time.mktime(value.utctimetuple()) * 1000
            ms += getattr(value, 'microseconds', 0) / 1000
            output[key] = int(ms)
        elif isinstance(value, db.GeoPt):
            output[key] = {'lat': value.lat, 'lon': value.lon}
        elif isinstance(value, db.Model):
            output[key] = value.key().id()
        else:
            raise ValueError('cannot encode ' + repr(prop))

    output['id'] = model.key().id()
    return output


def typify(model_class, attrs):
    """set data in correct type according to model declaration"""
    typified_attrs = {}
    for key, value in attrs.iteritems():
        log.info("key=%s, value=%s" % (key, value))
        if hasattr(model_class, key):
            attr = getattr(model_class, key)
            typified_value = value
            if not typified_value is None:
                if isinstance(attr, db.DateTimeProperty):
                    typified_value = datetime.fromtimestamp(int(value)/1000)
                elif isinstance(attr, db.IntegerProperty):
                    typified_value = int(value)
                elif isinstance(attr, db.ReferenceProperty):
                    typified_value =  db.Key.from_path(attr.reference_class.__name__, int(value))
                typified_attrs[key] = typified_value

    return typified_attrs

class RestifyMiddleware(object):

    def __init__(self, app, model_class, path, modifier = None):
        self.app = app
        self.model_class = model_class
        self.path = path
        self.modifier = modifier

    def get_body_dict(self, environ):
        length = int(environ.get('CONTENT_LENGTH', '0'))
        json_body = StringIO(environ['wsgi.input'].read(length)).getvalue()
        log.info("received json body %s", json_body)
        attrs = json.loads(json_body)
        #convert from unicode
        return dict((str(key), value) for key, value in attrs.iteritems())

    def get(self, environ, start_response, modifier):
        path = environ['PATH_INFO']
        path = path.split('/')
        if path[-1] == 'list':
            start_response('200 OK', [('Content-Type', 'application/json')])
            model_list = self.model_class.all()
            limit = 10
            if modifier and modifier.get('GET'):
                modifier_list = modifier.get('GET').get('list')
                if modifier_list:
                    limit = modifier_list.get('limit', 10)

            query = environ["QUERY_STRING"]
            query_dict = urlparse.parse_qs(query)
            limit = query_dict.get("limit", [limit])[0]
            limit = int(limit)
            limit = min([100, limit])

            order = query_dict.get("order", ['-__key__'])
            model_list.order(order[0])
            _filter = query_dict.get("filter", False)
            if _filter:
                _filter = json.loads(_filter[0])
                for key, value in _filter.iteritems():
                    attr = getattr(self.model_class, key)
                    if isinstance(attr, db.ReferenceProperty):
                        value = db.Key.from_path(attr.reference_class.__name__, int(value))
                    model_list.filter("%s =" % (key, ), value)

            page = int(query_dict.get("page", ['0'])[0])
            offset = page * limit
            result = [json.dumps([to_dict(instance) for instance in model_list.fetch(limit = limit, offset = offset)])]
            return result
        else:
            instance_id = int(path[-1])
            instance = self.model_class.get_by_id(instance_id)
            if instance:
                start_response('200 OK', [('Content-Type', 'application/json')])
                return [json.dumps(to_dict(instance))]
            else:
                start_response('404 Not found', [('Content-Type', 'text/plain')])

    def post(self, environ, start_response, modifier):
        start_response('200 OK', [('Content-Type', 'application/json')])

        attrs = self.get_body_dict(environ)
        if modifier and modifier.get('POST'):
            attrs = modifier.get('POST')(attrs)
            log.info("modifier returns %s", attrs)
            if attrs:
                return [json.dumps(to_dict(attrs))]

        new_object = self.model_class(**attrs)
        new_object.put()

        return [json.dumps(to_dict(new_object))]

    def put(self, environ, start_response, modifier):
        attrs = self.get_body_dict(environ)
        if modifier and modifier.get('PUT'):
            start_response('200 OK', [('Content-Type', 'application/json')])
            attrs = modifier.get('PUT')(attrs)
            log.info("modifier returns %s", attrs)
            if attrs:
                return [json.dumps(to_dict(attrs))]

        instance = self.model_class.get_by_id(attrs['id'])
        if instance:
            start_response('200 OK', [('Content-Type', 'application/json')])
            for key, value in typify(self.model_class, attrs).iteritems():
                log.info("setting %s to %s" % (key, value))
                if key != 'id':
                    #this will never work must be of correct type
                    setattr(instance, key, value)
            instance.put()
            return [json.dumps(to_dict(instance))]
        else:
            start_response('404 Not found', [('Content-Type', 'text/plain')])
        return ['']

    def delete(self, environ, start_response, modifier):
        path = environ['PATH_INFO'].split('/')
        instance_id = int(path[-1])
        instance = self.model_class.get_by_id(instance_id)
        if instance:
            start_response('200 OK', [('Content-Type', 'application/json')])
            instance.delete()
        else:
            log.info("404")
            start_response('404 Not found', [('Content-Type', 'text/plain')])
        return ['']

    def __call__(self, environ, start_response):
        if environ['PATH_INFO'].startswith("%s" % (self.path, )):
            modifier = self.modifier
            if modifier and modifier.get('ALL'):
                modifier.get('ALL')()
            if environ['REQUEST_METHOD'] == 'POST':
                return self.post(environ, start_response, modifier)
            elif environ['REQUEST_METHOD'] == 'GET':
                return self.get(environ, start_response, modifier)
            elif environ['REQUEST_METHOD'] == 'PUT':
                return self.put(environ, start_response, modifier)
            elif environ['REQUEST_METHOD'] == 'DELETE':
                return self.delete(environ, start_response, modifier)
            else:
                start_response('405 Method Not Allowed', [('Content-Type', 'text/plain')])
            return ['']

        return self.app(environ, start_response)
