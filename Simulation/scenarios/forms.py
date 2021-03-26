from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, \
                    DateField, DecimalField, SelectField
from wtforms.validators import InputRequired, NumberRange
from wtforms.widgets import TextArea
from datetime import date

class ScenarioForm(FlaskForm):
    title = StringField(label='Title',
                        validators=[InputRequired(message='Title is required')])
    birthdate = DateField(label='Date of birth (MM-DD-YYYY)',
                          format='%m-%d-%Y',
                          validators=[InputRequired(message='Required')],
                          default=date(month=1, day=1, year=2000))
    s_birthdate = DateField(label='Date of birth(MM-DD-YYYY)',
                            format='%m-%d-%Y',
                            default=date(month=1, day=1, year=2000))

    current_income = IntegerField(label='Current income',
                                  validators=[InputRequired(message='Required(can be 0)')],
                                  default=50000)
    s_current_income = IntegerField(label="Spouse's current income", default=50000)

    savings_rate = DecimalField(label='Savings rate',
                                  validators=[InputRequired(message='Required(can be 0)')],
                                default=15)
    s_savings_rate = DecimalField(label="Spouse's spouse's savings rate", default=15)

    ss_date = DateField(label='Date you will take Social Security (MM-DD-YYYY)',
                        format='%m-%d-%Y',
                        validators=[InputRequired(message='Required')],
                        default=date(month=1, day=1, year=2065))
    s_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY)',
                          format='%m-%d-%Y',
                          default=date(month=1, day=1, year=2065))

    ss_amount = IntegerField(label='SS amount',
                             validators=[InputRequired(message='Required(can be 0)')],
                             default=60000)
    s_ss_amount = IntegerField(label="Spouse's SS amount", default=60000)

    retirement_age = IntegerField(label='Retirement age',
                                  validators=[NumberRange(min=35, max=100,
                                                          message='Must be between 35 and 100')],
                                  default=65)
    s_retirement_age = IntegerField(label="Spouse's retirement age", default=65)

    ret_income = IntegerField(label='Retirement income',
                              validators=[InputRequired(message='Required(can be 0)')],
                              default=100000)
    s_ret_income = IntegerField(label="Spouse's retirement income", default=100000)

    ret_job_ret_age = IntegerField(label='Age at which you will fully retire',
                                   validators=[InputRequired(message='Required')], default=70)
    s_ret_job_ret_age = IntegerField(label='Age at which your spouse will fully retire', default=70)

    lifespan_age = IntegerField(label='Expected lifespan in years',
                                validators=[InputRequired(message='Required(can be 0)')], default=95)
    s_lifespan_age = IntegerField(label="Spouse's expected lifespan in years", default=95)

    windfall_amount = IntegerField(label='Windfall amount',
                                   validators=[NumberRange(min=0, max=1000000000,
                                                           message='Windfall amount must be between 0 and 1,000,000,000')],
                                   default=1000000)
    windfall_age = IntegerField(label='Windfall age',
                                validators=[NumberRange(min=30, max=100,
                                                        message='Windfall amount must be between 30 and 100')],
                                default=65)

    nestegg = IntegerField(label="Your investable savings",
                           validators=[InputRequired(message='Required(can be 0)')], default=100000)
    ret_spend = IntegerField(label="Expected annual spending in retirement",
                             validators=[InputRequired(message='Required')], default=150000)
    has_spouse = BooleanField(label='Married', default=False)

    investment = SelectField(label='Investment', coerce=int, validate_choice=False)

    submit = SubmitField('Save')
    cancel = SubmitField('Cancel', render_kw={'formnovalidate': True})

class DisplaySimResultForm(FlaskForm):
    title = StringField()

    taf = StringField(widget=TextArea(), render_kw={'readonly': True, 'rows': 2})

    submit = SubmitField('Close')

class DisplayAllSimResultForm(FlaskForm):
    title = StringField()
    submit = SubmitField('Close')