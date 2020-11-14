from datetime import datetime, date
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from Simulation.extensions import login_manager
from flask_login import UserMixin
from flask import current_app
from Simulation.extensions import db
from Simulation.users.utils import calculate_age


import matplotlib.pyplot as plt
import pandas as pd
import numpy as np

@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))

# The User class holds the account information
class User(db.Model, UserMixin):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    # User attributes needed for simulations
    scenarios = db.relationship('Scenario', backref='author', lazy=True)
    userdata = db.relationship('UserData', back_populates="user", uselist=False, lazy=True)


# The UserData class holds "constant" user information used in the simulations
# "Constant" is not strictly true. The idea is that the variables in this class don't change
# on a scenario by scenario basis. For example, current_income is typically a "set" value. Of course
# it may change if you take a new job, but most scenarios will be based on a user's actual current income
class UserData(db.Model):
    id = db.Column(db.Integer, db.ForeignKey('user.id'), primary_key=True)
    user = db.relationship('User', back_populates="userdata", uselist=False, lazy=True)
    title = db.Column(db.String(100), nullable=True)
    birthdate = db.Column(db.Date, nullable=False)
    current_age = db.Column(db.Integer, nullable=False) # Calculated every time we need it
    current_income = db.Column(db.Integer, nullable=False)
    lifespan_age = db.Column(db.Integer, nullable=False)
    full_ss_date = db.Column(db.Date, nullable=False)    #Calculate this from the birthdate
    full_ss_amount = db.Column(db.Integer, nullable=False)
    nestegg = db.Column(db.Integer, nullable=False)
    drawdown = db.Column(db.Integer, nullable=False)

    # Information for spouse
    has_spouse = db.Column(db.Boolean, nullable=False)
    s_birthdate = db.Column(db.Date, nullable=True)
    s_current_age = db.Column(db.Integer, nullable=True) # Calculated every time we need it
    s_current_income = db.Column(db.Integer, nullable=True)
    s_lifespan_age = db.Column(db.Integer, nullable=True)
    s_full_ss_date = db.Column(db.Date, nullable=True)  #Calculate this from the birthdate
    s_full_ss_amount = db.Column(db.Integer, nullable=True)

    # Need to add large ticket expenses (remodeling, weddings, etc.)

    def __repr__(self):
        return f"UserData('{self.birthdate}', '{self.current_age}')"

def get_reset_token(self, expires_sec=1800):
    s = Serializer(current_app.config['SECRET_KEY'], expires_sec)
    return s.dumps({'user_id': self.id}).decode('utf-8')

@staticmethod
def verify_reset_token(token):
    s = Serializer(current_app.config['SECRET_KEY'])
    try:
        user_id = s.loads(token)['user_id']
    except:
        return None
    return User.query.get(user_id)

def __repr__(self):
    return f"User('{self.username}', '{self.email}', '{self.image_file}')"


class Post(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    content = db.Column(db.Text, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    def __repr__(self):
        return f"Post('{self.title}', '{self.date_posted}')"

# Scenarios hold "variable" user information for the simulations. They are variable b/c the user may want to
# change them to see how they impact their simulation outcomes
class Scenario(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    title = db.Column(db.String(100), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    total_amount = db.Column(db.Float, nullable=False)
    asset_class = db.Column(db.String(20), nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)

    retirement_age = db.Column(db.DateTime, nullable=False)
    start_ss_date = db.Column(db.Date, nullable=False)
    ret_income = db.Column(db.Integer, nullable=False)
    ret_job_ret_date = db.Column(db.Date, nullable=False)
    windfall_amount = db.Column(db.Integer, nullable=False)
    windfall_age = db.Column(db.DateTime, nullable=False)

    # Need to add large ticket expenses (remodeling, weddings, etc.)
    large_1time_expenses = []

    s_retirement_age = db.Column(db.DateTime, nullable=False)
    s_start_ss_date = db.Column(db.DateTime, nullable=False)
    s_ret_income = db.Column(db.Integer, nullable=False)
    s_ret_job_ret_date = db.Column(db.Date, nullable=False)
    s_windfall_amount = db.Column(db.Integer, nullable=False)
    s_windfall_age = db.Column(db.DateTime, nullable=False)

    # Expand the fields to be printed as necessary
    def __repr__(self):
        return f"Scenario('{self.title}', '{self.date_posted}')"

# These data are kept in an object for convenience. They typically don't change
class sim_data():
    num_exp = 10000
    num_sim_bins = 100
    cola = 1.02
    inflation = [[1.027, 0.011]]
    asset_classes = []
    spend_decay = [[0.02, 0.001]]


def init_db(app):
    db.create_all()
    db.app = app