from dateutil.relativedelta import relativedelta
from Simulation.models import AssetClass
from wtforms import SelectField


# Given an index, get the AssetClass
def get_asset_class(asset_class_id: int):

    # Populate the investment asset classes dropdown
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    item = next(ac for ac in asset_class_list if ac.id == asset_class_id)
    return item


def populate_investment_dropdown(investment, asset_class_id=0):

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
def get_investment_from_select_field(investment : SelectField):

    # Populate the investment asset classes from the database
    asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
    asset_class_id = int(investment.raw_data[0])
    item = next(ac for ac in asset_class_list if ac.id == asset_class_id)
    return item.id, item


# Calculate age in years given two dates
def calculate_age(date1, date2):
    return date1.year - date2.year - ((date1.month, date1.day) < (date2.month, date2.day))


# Currently unused
def calculate_full_ss_date(birthday):
    if birthday.year <= 1937:
        year = 65
        month = 0
    elif birthday.year == 1938:
        year = 65
        month = 2
    elif birthday.year == 1939:
        year = 65
        month = 4
    elif birthday.year == 1940:
        year = 65
        month = 6
    elif birthday.year == 1941:
        year = 65
        month = 8
    elif birthday.year == 1942:
        year = 65
        month = 10
    elif (birthday.year >= 1943) and (birthday.year <= 1954):
        year = 66
        month = 0
    elif birthday.year == 1955:
        year = 66
        month = 2
    elif birthday.year == 1956:
        year = 66
        month = 4
    elif birthday.year == 1957:
        year = 66
        month = 6
    elif birthday.year == 1958:
        year = 66
        month = 8
    elif birthday.year == 1959:
        year = 66
        month = 10
    elif birthday.year >= 1960:
        year = 67
        month = 00
    full_ss_date = birthday + relativedelta(years=year, months=month)
    return full_ss_date




def get_key(dict, val):
    for key, value in dict.items():
        if val == value:
            return key
    return "NoKey"

def does_key_exist(dict, chk_key):
    for key, value in dict.items():
        if key == chk_key:
            return True
    return False