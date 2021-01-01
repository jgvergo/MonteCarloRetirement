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

def populateInvestmentDropdown(investment, asset_class_id = 0):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    titles = []
    for asset_class in asset_class_list:
        titles.append((asset_class.id, asset_class.title))

    # Set up the SelectField dropdown
    investment.choices = titles
    investment.data = asset_class_id
    return

# Get the currently selected asset class data from the SelectField dropdown
def getInvestmentDataFromSelectField(investment : SelectField):

    # Populate the investment asset classes from the database
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    asset_class_id = int(investment.raw_data[0])
    item = next(ac for ac in asset_class_list if ac.id == asset_class_id)
    return item.id, item


# Given an index, get the AssetClass
def getAssetClass(asset_class_id : int):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    item = next(ac for ac in asset_class_list if ac.id == asset_class_id)
    return item
