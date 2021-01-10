from Simulation.config import Config
from flask import Flask
from Simulation.extensions import db, bcrypt, login_manager, mail
from Simulation.models import init_db, AssetClass, Scenario, User, AssetMix, AssetMixAssetClass, SimData
from Simulation.utils import calculate_age
from datetime import date
import pandas as pd


sd = SimData()


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
    from Simulation.asset_mixes.routes import asset_mixes
    from Simulation.errors.handlers import errors

    app.register_blueprint(main)
    app.register_blueprint(users)
    app.register_blueprint(posts)
    app.register_blueprint(scenarios)
    app.register_blueprint(asset_classes)
    app.register_blueprint(asset_mixes)
    app.register_blueprint(errors)

    initDatabase()

    return app


# The following function re-initializes the database with some useful data
# It is only here as a convenience for development and debugging
def initDatabase():
    ac_list = AssetClass.query.count()
    if ac_list == 0:
        ac_df = pd.read_excel('AssetClassesMixes.xls', sheet_name='AssetClasses')
        m_index = ac_df.index[ac_df['Year'] == 'Mean'].tolist()
        sd_index = ac_df.index[ac_df['Year'] == 'Standard Deviation'].tolist()
        for column in ac_df:
            if ac_df[column].name == 'Year':
                pass
            elif ac_df[column].name == 'Inflation':
                sd.inflation[0] = ac_df[column][m_index[0]]
                sd.inflation[1] = ac_df[column][sd_index[0]]

            elif ac_df[column].name != 'Year':

                asset_class = AssetClass()
                asset_class.title = ac_df[column].name
                asset_class.avg_ret = ac_df[column][m_index[0]]
                asset_class.std_dev = ac_df[column][sd_index[0]]
                db.session.add(asset_class)
            else:
                exit()

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
        # Create user
        hashed_password = bcrypt.generate_password_hash('foobar2020').decode('utf-8')
        user = User(username='jgvergo', email='jgvergo@gmail.com', password=hashed_password)
        user.id = 1
        db.session.add(user)
        db.session.commit()

        # Create a single, "current scenario"
        scenario = Scenario()
        scenario.user_id = user.id
        scenario.title = 'Current scenario 12-12-2020'

        scenario.birthdate = date(month=10, day=18, year=1957)
        scenario.s_birthdate = date(month=2, day=12, year=1960)

        scenario.current_income = 0
        scenario.s_current_income = 0

        scenario.savings_rate = 0
        scenario.s_savings_rate = 0

        scenario.ss_date = date(month=10, day=18, year=2027)
        scenario.s_ss_date = date(month=2, day=12, year=2030)

        scenario.ss_amount = 45612
        scenario.s_ss_amount = 37476

        scenario.retirement_age = 62
        scenario.s_retirement_age = 59

        scenario.ret_income = 0
        scenario.s_ret_income = 0

        scenario.ret_job_ret_age = 68
        scenario.s_ret_job_ret_age = 65

        scenario.lifespan_age = 95
        scenario.s_lifespan_age = 95

        scenario.windfall_amount = 4000000
        scenario.windfall_age = 70

        scenario.has_spouse = True
        scenario.nestegg = 2500000
        scenario.drawdown = 150000

        # Calculate ages from birthdates and save the,
        scenario.current_age = calculate_age(date.today(), scenario.birthdate)
        if (scenario.has_spouse):
            scenario.s_current_age = calculate_age(date.today(), scenario.s_birthdate)
        am = AssetMix.query.filter_by(title='JeffW').first()
        scenario.asset_mix_id = am.id
        db.session.add(scenario)
        db.session.commit()

    return