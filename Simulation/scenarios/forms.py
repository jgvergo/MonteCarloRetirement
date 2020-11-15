from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, RadioField, IntegerField, DateField
from wtforms.validators import InputRequired, NumberRange, AnyOf


class ScenarioForm(FlaskForm):
    title = StringField(label='Title',
                        validators=[InputRequired(message='Title is required')])
    total_amount = DecimalField(label='Total amount:',
                                validators=[NumberRange(min=0, max=100000000,
                                message='Amount must be between 0 and 100,000,000')])
    asset_class = RadioField(label='Asset Class',
                             choices=['S&P500', 'Nasdaq', 'Dow', 'Other'],
                             validators=[AnyOf(['S&P500', 'Nasdaq', 'Dow', 'Other'],
                                               message='Must be AnyOf the choices')])
    retirement_age = IntegerField(label='Retirement age:',
                                validators=[NumberRange(min=35, max=100,
                                message='Retirement age must be between 35 and 100')])
    start_ss_date = DateField(label='Date you will take Social Security(MM-DD-YYYY):',
                              format='%m-%d-%Y',
                              validators = [InputRequired(message='Required')])
    ret_income = IntegerField(label='Retirement income:',
                              validators=[InputRequired(message='Required(can be 0)')])
    ret_job_ret_date = DateField(label='Date you will retire from your retirement job(MM-DD-YYYY):',
                              format='%m-%d-%Y',
                              validators = [InputRequired(message='Required')])
    windfall_amount = IntegerField(label='Windfall amount:',
                                validators=[NumberRange(min=0, max=1000000000,
                                message='Windfall amount must be between 0 and 1,000,000,000')])
    windfall_age = IntegerField(label='Windfall age:',
                                validators=[NumberRange(min = 30, max=100,
                                message='Windfall amount must be between 30 and 100')])
    s_retirement_age = IntegerField(label="Spouse's_retirement_age etirement age:",
                                validators=[NumberRange(min=35, max=100,
                                message="Spouse's retirement age must be between 35 and 100")])
    s_start_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY):',
                              format='%m-%d-%Y',
                              validators = [InputRequired(message='Required')])
    s_ret_income = IntegerField(label="Spouse's retirement income:",
                              validators=[InputRequired(message='Required(can be 0)')])
    s_ret_job_ret_date = DateField(label='Date your spouse will retire from his/her retirement job(MM-DD-YYYY):',
                              format='%m-%d-%Y',
                              validators = [InputRequired(message='Required')])
    s_windfall_amount = IntegerField(label="Spouse's windfall amount:",
                                validators=[NumberRange(min=0, max=1000000000,
                                message='Windfall amount must be between 0 and 1,000,000,000')])
    s_windfall_age = IntegerField(label="Spouse's windfall age:",
                                validators=[NumberRange(min = 30, max=100,
                                message='Windfall amount must be between 30 and 100')])

    submit = SubmitField('Save')


class DisplaySimResultForm(FlaskForm):
    title = StringField(label='Scenario title',
                        validators=[InputRequired(message='Title is required')])
    submit = SubmitField('Home')