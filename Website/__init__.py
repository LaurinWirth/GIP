from flask import Flask 
from flask_sqlalchemy import SQLAlchemy
from os import path
from flask_login import LoginManager, login_manager

db = SQLAlchemy()
DB_NAME = "database.db"

def create_app():
    app=Flask(__name__)
    app.config['SECRET_KEY'] = 'pIphvb0IDXOoPZO2XFLS'
    app.config['SQLALCHEMY_DATABASE_URI'] = 'postgresql://cviowhzivhgjeq:f3c7ef52185515b1af6b6b5c5ee7f99c8b9d166ca4416743b0512b2557c569aa@ec2-54-205-232-84.compute-1.amazonaws.com:5432/dbcnhlqqfu9jl7'
    db.init_app(app)

    
    from .views import views
    from .auth import auth

    app.register_blueprint(views, url_prefix='/')
    app.register_blueprint(auth, url_prefix='/')

    from .models import User, Donation


    create_database(app)

    login_manager = LoginManager()
    login_manager.login_view = 'auth.login'
    login_manager.init_app(app)

    @login_manager.user_loader 
    def load_user(id):
        return User.query.get(int(id))

    return app 

def create_database(app):
    if not path.exists('website/' + DB_NAME):
        db.create_all(app=app)
        print('Created Database!')
