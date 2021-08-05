from datetime import date
from logging import error
from flask import Blueprint, request, flash, redirect, url_for, session
from flask.templating import render_template
from sqlalchemy.engine import url
from sqlalchemy.sql.functions import user
from .models import User
from .models import Donation
from werkzeug.security import generate_password_hash, check_password_hash
from .import db
from flask_login import login_user, login_required, logout_user, current_user 
import hashlib


auth = Blueprint('auth', __name__)

@auth.route('/login', methods = ['GET', 'POST'])
def login():
    if request.method == 'POST':

        email = request.form.get('email')
        password = request.form.get('password1')

        user = User.query.filter_by(email=email).first()

        if user: 
            if check_password_hash(user.password, password): 
                login_user(user, remember=True)
                return redirect(url_for('views.configureDashboard'))
            else: 
                flash('Incorrect Password, try again', category='error')
        else: 
          flash('Email does not exist.', category='error')
    return render_template('login.html', user=current_user)

@auth.route('/logout')
@login_required
def logout(): 
    logout_user()
    return redirect (url_for('auth.login'))
    

@auth.route('/signup', methods = ['GET', 'POST'])
def sig_up(): 
    if request.method == 'POST': 
        email = request.form.get('email')
        password1 = request.form.get('password1')
        password2 = request.form.get('password2')
        first_name = request.form.get('fullname')
        type = request.form.get('radio')
        

        user = User.query.filter_by(email = email).first()

        if user: 
            flash('This Email already exists', category='error')
        elif len(first_name) < 3: 
            flash('User name must be greater than 2 characters', category='error')
        elif len(email) < 8: 
            flash ('Please user a valid email address', category='error')
        elif password1 != password2: 
            flash('passwords don\'t match.',category='error')
        else: 
            new_user = User(email=email, first_name=first_name, password=generate_password_hash(password1, method='sha256'), type=type)
            db.session.add(new_user)
            db.session.commit()
            # login_user(user, remember=True)
            flash('Your account was successfully created.', category='succcess')
            
            return redirect(url_for('auth.login'))
        

    return render_template('signup.html', user=current_user)


@auth.route('/dashboard/<uniqueId>')
@login_required
def dashboard(uniqueId):
    
    user = current_user.email
    uniqueId = int(hashlib.sha256(user.encode('utf-8')).hexdigest(), 16) % 10**8

    return render_template('dashboard.html')

    # password=generate_password_hash(password1, method='sha256')
    # print(username)
    # return render_template('dashboard.html')
