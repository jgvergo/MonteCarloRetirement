from Simulation.config import Config
from flask import Flask
from Simulation.extensions import db, bcrypt, login_manager, mail
from Simulation.models import init_db, AssetClass, Scenario, User, AssetMix, AssetMixAssetClass
from Simulation.utils import calculate_age
from datetime import date

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
        ac_data=[['', 0, 0],  # This is the "default" asset class shown to users when they add one to an Asset Mix
                 ['1-5yr High Yield Bonds', 0.0671, 0.01],
                 ['3% Fixed', 0.03, 0.0],
                 ['4% Fixed', 0.04, 0.0],
                 ['5% Fixed', 0.05, 0.0],
                 ['Corporate Bonds', 0.055, 0.0526],
                 ['Dividend-Paying Equity', 0.1181, 0.1024],
                 ['Dow Jones Industrial Average', 0.0818, 0.2059],
                 ['Emerging Markets Equity', 0.0089, 0.1695],
                 ['Global Commodities', -0.0538, 0.166],
                 ['Global Equity', 0.0675, 0.125],
                 ['Global Equity - ESG Leaders', 0.0687, 0.1203],
                 ['Global Listed Private Equity', 0.0559, 0.1863],
                 ['Hedge Funds', 0.0405, 0.057],
                 ['Investment Grade Bonds', 0.0317, 0.0292],
                 ['Jeff Wenzel (estimated)', 0.07, 0.04],
                 ['Nasdaq', 0.1308, 0.2541],
                 ['Real Estate Investment Trusts', 0.0844, 0.1103],
                 ['S&P500', 0.1153, 0.1962],
                 ['Taxable Municipal Bonds', 0.072, 0.0733],
                 ['Treasury Coupons (1 Year)', 0.0073, 0.0081],
                 ['Treasury Coupons (30 Day)', 0.0012, 0.00144],
                 ['U.S. Large Cap Equity', 0.1122, 0.1139],
                 ['U.S. Mid Cap Equity', 0.11, 0.136],
                 ['U.S. Small Cap Equity', 0.1187, 0.1446]
                ]
        for i in range(len(ac_data)):
            asset_class = AssetClass()
            asset_class.title = ac_data[i][0]
            asset_class.avg_ret = ac_data[i][1]
            asset_class.std_dev = ac_data[i][2]
            db.session.add(asset_class)
        # Create user
        hashed_password = bcrypt.generate_password_hash('foobar2020').decode('utf-8')
        user = User(username='jgvergo', email='jgvergo@gmail.com', password=hashed_password)
        user.id = 1
        db.session.add(user)


        # Create a single, current scenario
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

        scenario.ret_income = 15000
        scenario.s_ret_income = 5000

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

        scenario.asset_mix_id = 6
        db.session.add(scenario)
        db.session.commit()

    # If the asset_mix table is empty, add the canonical mixes from Fidelity
    am_list = AssetMix.query.count()
    if am_list == 0:
        # AssetClass 17 = S&P 500
        # AssetClass 10 = Global Equity
        # AssetClass 14 = Investment Grade Bonds
        # AssetClass 20 = 30-Day Treasuries
        am_data = [['Lowest risk', '',        [[21, 100]]],
                   ['Conservative', '',       [[18, 14], [11, 6],  [15, 50], [21, 30]]],
                   ['Moderate w/ income', '', [[18, 21], [11, 9],  [15, 50], [21, 20]]],
                   ['Moderate', '',           [[18, 28], [11, 12], [15, 45], [21, 15]]],
                   ['Balanced', '',           [[18, 35], [11, 15], [15, 40], [21, 10]]],
                   ['Growth w/ income', '',   [[18, 42], [11, 18], [15, 35], [21, 5]]],
                   ['Growth', '',             [[18, 49], [11, 21], [15, 25], [21, 5]]],
                   ['Aggressive growth', '',  [[18, 60], [11, 25], [15, 15]]],
                   ['Most aggressive', '',    [[18, 70], [11, 30]]]]
        for i in range(len(am_data)):
            asset_mix = AssetMix()
            asset_mix.title = am_data[i][0]
            asset_mix.description = am_data[i][1]
            db.session.add(asset_mix)

            for amac in am_data[i][2]:
                asset_mix_asset_class = AssetMixAssetClass()
                asset_mix_asset_class.asset_mix_id = i+1  # Should be asset_mix.id
                asset_mix_asset_class.asset_class_id = amac[0]
                asset_mix_asset_class.percentage = amac[1]
                db.session.add(asset_mix_asset_class)
        db.session.commit()
    return