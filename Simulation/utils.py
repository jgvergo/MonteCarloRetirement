from dateutil.relativedelta import relativedelta
from Simulation.models import AssetClass, AssetMix, AssetMixAssetClass
from wtforms import SelectField
import os
import inspect, logging
import ntpath


def get_invest_data(id, assetmix):
    invest = []
    # The variable assetmix indicates if we are getting AssetMix data. If not, we are getting a single AssetClass
    if assetmix:
        amac_list = AssetMixAssetClass.query.filter_by(asset_mix_id=id).all()
        for amac in amac_list:
            ac = AssetClass.query.filter_by(id=amac.asset_class_id).first()
            invest.append([ac.title, amac.percentage])
    else:
        ac = AssetClass.query.filter_by(id=id).first()
        invest.append([ac.title, 100.0])
    return invest

# Given an index, get the AssetClass
def get_asset_class(asset_class_id: int):

    # Get the full set and search for the one that matches the id
    asset_class_list = AssetClass.query.all()
    item = next(ac for ac in asset_class_list if ac.id == asset_class_id)
    return item


# Given an index, get the AssetMix
def get_asset_mix(asset_mix_id: int):

    # Get the full set and search for the one that matches the id
    asset_mix_list = AssetMix.query.all()
    for am in asset_mix_list:
        if am.id == asset_mix_id:
            mcr_log('Found am {}'.format(am.id), 'info')
            return am
    mcr_log('Non-existent asset mix', 'error')



def populate_investment_dropdown(sf, id=0, kind='AssetMix'):
    titles = []
    # Populate the investment asset mixes dropdown
    if kind == 'AssetMix':
        asset_mix_list = AssetMix.query.order_by(AssetMix.title.asc())
        for asset_mix in asset_mix_list:
            titles.append((asset_mix.id, asset_mix.title))
    elif kind == 'AssetClass':
        asset_class_list = AssetClass.query.order_by(AssetClass.title.asc())
        for asset_class in asset_class_list:
            titles.append((asset_class.id, asset_class.title))
    else:
        mcr_log('Unknown kind of investment', 'error')
    # Set up the SelectField dropdown
    sf.choices = titles
    sf.data = id
    return


# Get the currently selected asset mix data from the SelectField dropdown
def get_investment_from_select_field(investment: SelectField):

    # Populate the investment asset mixes from the database
    asset_mix_list = AssetMix.query.order_by(AssetMix.title.asc())
    asset_mix_id = int(investment.raw_data[0])
    item = next(am for am in asset_mix_list if am.id == asset_mix_id)
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

# create logger
logger = logging.getLogger('mcr_web_logger')
ch = logging.StreamHandler()

logLevel = os.getenv("MCR_LOG_LEVEL", 'DEBUG')

if logLevel == 'NOTSET':
    logger.setLevel(logging.NOTSET)
    ch.setLevel(logging.NOTSET)
elif logLevel == 'INFO':
    logger.setLevel(logging.INFO)
    ch.setLevel(logging.INFO)
elif logLevel == 'DEBUG':
    logger.setLevel(logging.DEBUG)
    ch.setLevel(logging.DEBUG)
elif logLevel == 'WARNING':
    logger.setLevel(logging.WARNING)
    ch.setLevel(logging.WARNING)
elif logLevel == 'CRITICAL':
    logger.setLevel(logging.CRITICAL)
    ch.setLevel(logging.CRITICAL)
elif logLevel == 'ERROR':
    logger.setLevel(logging.ERROR)
    ch.setLevel(logging.ERROR)


# create formatter
formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')

# add formatter to ch
ch.setFormatter(formatter)

# add ch to logger
logger.addHandler(ch)

# This is the function that should be called from other application code
def mcr_log(message, level):
    # Get the previous frame in the stack, otherwise it would be this function!!!
    func = inspect.currentframe().f_back.f_code
    logFunc = level_to_log(level)
    logFunc(message, func)

def level_to_log(argument):
    switcher = {
        'info': logInfo,
        'debug': logDebug,
        'warning': logWarning,
        'critical': logCritical,
        'error': logError
    }
    # Get the function from switcher dictionary
    logFunc = switcher.get(argument, lambda: "Invalid logging level")
    # Return the log function
    return logFunc


def logInfo(message, func):
    logger.info("Message = %s, Function name = %s, Filename = %s, Line number = %i" % (
        message,
        func.co_name,
        ntpath.basename(func.co_filename),
        func.co_firstlineno
    ))
    return


def logDebug(message, func):
    logger.debug("Message = %s, Function name = %s, Filename = %s, Line number = %i" % (
        message,
        func.co_name,
        ntpath.basename(func.co_filename),
        func.co_firstlineno
    ))
    return


def logWarning(message, func):
    logger.warning("Message = %s, Function name = %s, Filename = %s, Line number = %i" % (
        message,
        func.co_name,
        ntpath.basename(func.co_filename),
        func.co_firstlineno
    ))
    return


def logCritical(message, func):
    logger.critical("Message = %s, Function name = %s, Filename = %s, Line number = %i" % (
        message,
        func.co_name,
        ntpath.basename(func.co_filename),
        func.co_firstlineno
    ))
    return


def logError(message, func):
    logger.error("Message = %s, Function name = %s, Filename = %s, Line number = %i" % (
        message,
        func.co_name,
        ntpath.basename(func.co_filename),
        func.co_firstlineno
    ))
    return
