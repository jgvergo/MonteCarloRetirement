from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DecimalField, SelectField
from wtforms.validators import InputRequired
from Simulation.models import AssetClass, Scenario, User
from Simulation.extensions import db, bcrypt
from Simulation.users.utils import calculate_age
from datetime import date

class AssetClassForm(FlaskForm):
    title = StringField(label='Name of asset class', validators=[InputRequired(message='Required')])
    avg_ret = DecimalField(label='Average annual return', places=5,
                           number_format="{:.2%}", validators=[InputRequired(message='Required')])
    std_dev = DecimalField(label='Risk (standard deviation)', places=5, number_format="{:.2%}", validators=[InputRequired(message='Required')])
    submit = SubmitField('Save Asset Class')


class AssetClassListForm(FlaskForm):
    nas = SubmitField('New Asset Class')
    home = SubmitField('Home')

def populateInvestmentDropdown(investment, asset_class_id = 0):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    titles=[]
    for asset_class in asset_class_list:
        titles.append((asset_class.id, asset_class.title))

    # Set up the SelectField dropdown
    investment.choices=titles
    investment.data = asset_class_id
    return

# Get the currently selected asset class data from the SelectField dropdown
def getInvestmentDataFromSelectField(investment : SelectField):

    # Populate the investment asset classes from the database
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    asset_class_id = int(investment.data)
    for ac in asset_class_list:
        if ac.id == asset_class_id:
            return asset_class_id, ac


# Given an index, get the AssetClass
def getAssetClass(asset_class_id : int):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    for ac in asset_class_list:
        if ac.id == asset_class_id:
            return ac


def initDatabase():
    ac_list = AssetClass.query.count()
    if ac_list == 0:
        ac_data=[['1-5yr High Yield Bonds', 0.0671, 0.01],
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
                 ['Nasdaq', 0.1308, 0.2541],
                 ['Real Estate Investment Trusts', 0.0844, 0.1103],
                 ['S&P500', 0.1153, 0.1962],
                 ['Taxable Municipal Bonds', 0.072, 0.0733],
                 ['Treasury Coupons', 0.0073, 0.0081],
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
        scenario.title = 'Current - 12-12-2020'

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
        scenario.drawdown = 150

        # Calculate ages from birthdates and save the,
        scenario.current_age = calculate_age(date.today(), scenario.birthdate)
        if (scenario.has_spouse):
            scenario.s_current_age = calculate_age(date.today(), scenario.s_birthdate)

        scenario.asset_class_id = 1
        db.session.add(scenario)
        db.session.commit()
    return