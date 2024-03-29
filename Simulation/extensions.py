from flask_sqlalchemy import SQLAlchemy
from flask_login import LoginManager
from flask_mail import Mail
from flask_bcrypt import Bcrypt
from rq import Queue
from Worker import conn as redis_conn

bcrypt = Bcrypt()
login_manager = LoginManager()
login_manager.login_view = 'users.login'
login_manager.login_message_category = 'info'
mail = Mail()
db = SQLAlchemy()

# Initialize queue
q = Queue(connection=redis_conn)
