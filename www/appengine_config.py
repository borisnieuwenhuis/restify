import logging

from restify import RestifyMiddleware
from member import Member

def webapp_add_wsgi_middleware(app):
    app = RestifyMiddleware(app, Memer, '/member')
    return app
