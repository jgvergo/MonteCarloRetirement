from Simulation.config import Config
from flask import Flask
from Simulation.extensions import db, bcrypt, login_manager, mail
from Simulation.models import init_db


def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.app_context().push()

    db.init_app(app)
    init_db(app)

    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from Simulation.main.routes import main
    from Simulation.users.routes import users
    from Simulation.posts.routes import posts
    from Simulation.scenarios.routes import scenarios
    from Simulation.asset_classes.routes import asset_classes
    from Simulation.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(scenarios)
    app.register_blueprint(asset_classes)
    app.register_blueprint(errors)

    return app
