from Simulation.config import Config
from flask import Flask
from Simulation.extensions import db, bcrypt, login_manager, mail
from Simulation.models import AssetClass, Scenario, User, AssetMix, AssetMixAssetClass, SimData
from Simulation.utils import calculate_age
from datetime import date
import pandas as pd
#from sqlalchemy.engine import Engine
#from sqlalchemy import event


#  Solved a db concurrency problem
# See https://stackoverflow.com/questions/9671490/how-to-set-sqlite-pragma-statements-with-sqlalchemy
#@event.listens_for(Engine, "connect")
#def set_sqlite_pragma(dbapi_connection, connection_record):
#    cursor = dbapi_connection.cursor()
#    cursor.execute("PRAGMA journal_mode=WAL")
#    cursor.close()
#    connect_args = {'timeout': 15}

def create_app(config_class=Config):
    app = Flask(__name__)
    app.config.from_object(Config)
    app.app_context().push()

    db.init_app(app)
    db.create_all()


    bcrypt.init_app(app)
    login_manager.init_app(app)
    mail.init_app(app)

    from Simulation.main.routes import main
    from Simulation.users.routes import users
    from Simulation.posts.routes import posts
    from Simulation.scenarios.routes import scenarios
    from Simulation.asset_mixes.routes import asset_mixes
    from Simulation.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(scenarios)
    app.register_blueprint(asset_mixes)
    app.register_blueprint(errors)

    initDatabase()

    return app


# The following function re-initializes the database with some useful data
def initDatabase():
    # See if theSimData has already been created
    sd_count = SimData.query.count()
    if sd_count > 0:
        # If it has been created, use it
        sd = SimData.query.first()
    else:
        # otherwise, create a new db entry
        sd = SimData()

    sd.num_exp = 2000
    sd.num_sim_bins = 100
    sd.cola = [0.03632608696, 0.02904712979]
    sd.asset_classes = []
    sd.spend_decay = [0.00, 0.00]
    sd.debug = True

    if sd_count == 0:
        # If sd has not been initialized in the past...
        sd.ac_df = pd.read_excel('AssetClassesMixes.xls', sheet_name='AssetClasses')

        # Drop the Mean and Standard Deviation rows and the Year Column
        sd.ac_df = sd.ac_df[sd.ac_df.Year != 'Mean']
        sd.ac_df = sd.ac_df[sd.ac_df.Year != 'Standard Deviation']
        sd.ac_df.drop('Year', axis=1, inplace=True)

        # Calculate the means and covariance matrix once and save it
        sd.cov = sd.ac_df.cov()
        sd.mean = sd.ac_df.mean()

    if sd_count == 0:
        db.session.add(sd)
    db.session.commit()

    if AssetClass.query.count() == 0:
        # Save the AssetClass data in the database. The inflation data will be used in the simulation engine
        for column in sd.ac_df:
            if sd.ac_df[column].name == 'Inflation':
                pass
            else:
                asset_class = AssetClass()
                asset_class.title = sd.ac_df[column].name
                db.session.add(asset_class)
                db.session.commit()

        # Now that all the AssetClasses have been created, read and save the AssetMixes for the AssetMixes sheet
        # Note that the spreadsheet is constructed so that the asset names in this sheet reference the names in the
        # AssetClasses sheet and should therefore always match exactly
        am_df = pd.read_excel('AssetClassesMixes.xls', sheet_name='AssetMixes')
        for rindex, row in am_df.iterrows():
            am = AssetMix()
            for idx, item in enumerate(row):
                if isinstance(item, str):
                    am.title = item
                    am.description = ''
                    db.session.add(am)
                    db.session.commit()
                elif isinstance(item, float):
                    if not pd.isnull(item):
                        amac = AssetMixAssetClass()
                        amac.asset_mix_id = am.id

                        # Find the AssetClass by matching the title
                        ac = AssetClass.query.filter_by(title=row.index[idx]).first()
                        amac.asset_class_id = ac.id
                        amac.percentage = item
                        db.session.add(amac)
                        db.session.commit()
    if User.query.count() == 0:
        # Create user
        hashed_password = bcrypt.generate_password_hash('foobar2020').decode('utf-8')
        user = User(username='jgvergo', email='jgvergo@gmail.com', password=hashed_password)
        db.session.add(user)
        db.session.commit()

    if Scenario.query.count() == 0:
        # Create a single, "sample scenario"
        user = User.query.first()
        scenario = Scenario()
        scenario.user_id = user.id
        scenario.title = 'Sample scenario'

        scenario.birthdate = date(month=10, day=18, year=1957)
        scenario.s_birthdate = date(month=2, day=12, year=1960)

        scenario.current_income = 0
        scenario.s_current_income = 0

        scenario.savings_rate = 0
        scenario.s_savings_rate = 0

        scenario.ss_date = date(month=10, day=18, year=2027)
        scenario.s_ss_date = date(month=2, day=12, year=2030)

        scenario.ss_amount = 46000
        scenario.s_ss_amount = 37000

        scenario.retirement_age = 62
        scenario.s_retirement_age = 59

        scenario.ret_income = 0
        scenario.s_ret_income = 0

        scenario.ret_job_ret_age = 68
        scenario.s_ret_job_ret_age = 65

        scenario.lifespan_age = 95
        scenario.s_lifespan_age = 95

        scenario.windfall_amount = 1000000
        scenario.windfall_age = 70

        scenario.has_spouse = True
        scenario.nestegg = 1000000
        scenario.ret_spend = 150000

        # Calculate ages from birthdates and save the,
        scenario.current_age = calculate_age(date.today(), scenario.birthdate)
        if (scenario.has_spouse):
            scenario.s_current_age = calculate_age(date.today(), scenario.s_birthdate)
        am = AssetMix.query.filter_by(title='Stocks/Bonds 60/40').first()
        scenario.asset_mix_id = am.id
        db.session.add(scenario)
    db.session.commit()
