from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DecimalField, SelectField
from wtforms.validators import InputRequired
from Simulation.models import AssetClass
from Simulation.extensions import db

class AssetClassForm(FlaskForm):
    title = StringField(label='Name of asset class', validators=[InputRequired(message='Required')])
    avg_ret = DecimalField(label='Average annual return', places=5,
                           number_format="{:.2%}", validators=[InputRequired(message='Required')])
    std_dev = DecimalField(label='Risk (standard deviation)', places=5, number_format="{:.2%}", validators=[InputRequired(message='Required')])
    submit = SubmitField('Save Asset Class')


class AssetClassListForm(FlaskForm):
    nas = SubmitField('New Asset Class')
    home = SubmitField('Home')

def populateInvestmentDropdown(investment, ac_index = 0):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    titles=[]
    for i, asset_class in enumerate(asset_class_list):
        titles.append((i, asset_class.title))

    # Set up the SelectField dropdown
    investment.choices=titles
    investment.data = ac_index
    return

# Get the currently selected asset class data from the SelectField dropdown
def getInvestmentDataFromSelectField(investment : SelectField):

    # Populate the investment asset classes from the database
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    ac_index = int(investment.data)
    return ac_index, asset_class_list[ac_index]

# Given an index, get the AssetClass
def getAssetClass(ac_index : int):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    return asset_class_list[ac_index]

def initAssetClasses():
    ac_list = AssetClass.query.count()
    if ac_list == 0:
        ac_data=[['Global Commodities', -0.0538, 0.166],
                ['Emerging Markets Equity', 0.0089, 0.1695],
                ['Treasury Coupons', 0.0073, 0.0081],
                ['Investment Grade Bonds', 0.0317, 0.0292],
                ['Hedge Funds', 0.0405, 0.057],
                ['Corporate Bonds', 0.055, 0.0526],
                ['Global Listed Private Equity', 0.0559, 0.1863],
                ['1-5yr High Yield Bonds', 0.0671, 0.01],
                ['Global Equity', 0.0675, 0.125],
                ['Global Equity - ESG Leaders', 0.0687, 0.1203],
                ['Tabable Municiple Bonds', 0.072, 0.0733],
                ['Real Estate Investment Trusts', 0.0844, 0.1103],
                ['U.S. Mid Cap Equity', 0.11, 0.136],
                ['U.S. Large Cap Equity', 0.1122, 0.1139],
                ['Dividend-Paying Equity', 0.1181, 0.1024],
                ['U.S. Small Cap Equity', 0.1187, 0.1446],
                ['S&P500', 0.1153, 0.1962]
                ]
        for i in range(len(ac_data)):
            asset_class = AssetClass()
            asset_class.title = ac_data[i][0]
            asset_class.avg_ret = ac_data[i][1]
            asset_class.std_dev = ac_data[i][2]
            db.session.add(asset_class)

        db.session.commit()
    return