from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DecimalField, SelectField
from wtforms.validators import InputRequired
from Simulation.models import AssetClass


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