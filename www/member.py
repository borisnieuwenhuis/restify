from google.appengine.ext import db

class Member(db.Model):
    name = db.StringProperty(required = True)
