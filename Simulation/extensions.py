from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from rq import Queue
import os
import redis


bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()
db = SQLAlchemy()

# Initialize Redis
redis_url = os.getenv('REDISTOGO_URL', 'redis://localhost:6379')
redis_conn = redis.from_url(redis_url)
q = Queue(connection=redis_conn)

