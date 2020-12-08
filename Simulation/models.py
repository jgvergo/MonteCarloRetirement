from datetime import datetime
from itsdangerous import TimedJSONWebSignatureSerializer as Serializer
from Simulation.extensions import login_manager
from flask_login import UserMixin
from flask import current_app
from Simulation.extensions import db


@login_manager.user_loader
def load_user(user_id):
    return User.query.get(int(user_id))


# The User class holds the account information
class User(db.Model, UserMixin):
    # Housekeeping information
    id = db.Column(db.Integer, primary_key=True)

    username = db.Column(db.String(20), unique=True, nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')
    password = db.Column(db.String(60), nullable=False)
    posts = db.relationship('Post', backref='author', lazy=True)

    # User attributes needed for simulations
    scenarios = db.relationship('Scenario', backref='author', lazy=True)


# AssetClasses are investment vehicles.
class AssetClass(db.Model):
    # Housekeeping information
    id = db.Column(db.Integer, primary_key=True)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    title = db.Column(db.String(100), nullable=True)
    avg_ret = db.Column(db.Float, nullable=False)
    std_dev = db.Column(db.Float, nullable=False)

    def __repr__(self):
        return f"AssetClass('{self.title}', '{self.avg_ret}', '{self.std_dev})"


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


# Scenarios hold the information for a single simulation.
class Scenario(db.Model):
    # Housekeeping information
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    date_posted = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)

    title = db.Column(db.String(100), nullable=False)

    birthdate = db.Column(db.Date, nullable=False)
    s_birthdate = db.Column(db.Date, nullable=True)

    current_income = db.Column(db.Integer, nullable=False)
    s_current_income = db.Column(db.Integer, nullable=True)

    savings_rate = db.Column(db.Float, nullable=False)
    s_savings_rate = db.Column(db.Float, nullable=False)

    start_ss_date = db.Column(db.Date, nullable=False)
    s_start_ss_date = db.Column(db.Date, nullable=True)

    ss_amount = db.Column(db.Integer, nullable=False)
    s_ss_amount = db.Column(db.Integer, nullable=True)

    retirement_age = db.Column(db.Integer, nullable=False)
    s_retirement_age = db.Column(db.Integer, nullable=True)

    ret_income = db.Column(db.Integer, nullable=False)
    s_ret_income = db.Column(db.Integer, nullable=True)

    ret_job_ret_age = db.Column(db.Integer, nullable=False)
    s_ret_job_ret_age = db.Column(db.Integer, nullable=True)

    lifespan_age = db.Column(db.Integer, nullable=False)
    s_lifespan_age = db.Column(db.Integer, nullable=True)

    # Combined information for the two spouses
    windfall_amount = db.Column(db.Integer, nullable=False)
    windfall_age = db.Column(db.Integer, nullable=False)
    nestegg = db.Column(db.Integer, nullable=False)
    drawdown = db.Column(db.Integer, nullable=False)
    has_spouse = db.Column(db.Boolean, nullable=False)

    current_age = db.Column(db.Integer, nullable=False)  # Calculated every time we need it
    s_current_age = db.Column(db.Integer, nullable=True)  # Calculated every time we need it
    full_ss_date = db.Column(db.Date, nullable=False)    # Calculate this from the birthdate
    s_full_ss_date = db.Column(db.Date, nullable=True)  # Calculate this from the birthdate

    image_file = db.Column(db.String(20), nullable=False, default='default.jpg')

    # Expand the fields to be printed as necessary
    def __repr__(self):
        return f"Scenario('{self.title}', '{self.date_posted}')"


# These data are kept in an object for convenience. They typically don't change
class SimData:
    num_exp = 10000
    num_sim_bins = 100
    cola = 1.02
    inflation = [1.027, 0.011]
    asset_classes = []
    spend_decay = [0.02, 0.001]


def init_db(app):
    db.create_all()
    db.app = app
