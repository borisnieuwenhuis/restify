from google.appengine.ext.webapp.util import run_wsgi_app
from google.appengine.ext import webapp

def get_application():
    return webapp.WSGIApplication([], debug = True)

def main():
    run_wsgi_app(get_application())

if __name__ == "__main__":
    main()
