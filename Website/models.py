from . import db
from flask_login import UserMixin
from sqlalchemy.sql import func
from datetime import datetime, timezone

class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    email = db.Column(db.String(150), unique=True)
    password = db.Column(db.String(150))
    first_name = db.Column(db.String(150))
    type = db.Column(db.String(150))
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    donations = db.relationship('Donation')
 
    

class Donation(db.Model):
    id = db.Column (db.Integer, primary_key=True)
    amount = db.Column(db.Integer)
    description = db.Column(db.String)
    organisation = db.Column(db.String(250))
    date_donated = db.Column(db.Date)
    date_created = db.Column(db.DateTime(timezone=True), default=datetime.utcnow)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
