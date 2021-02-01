from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, \
                    DateField, DecimalField, SelectField
from wtforms.validators import InputRequired, NumberRange
from wtforms.widgets import TextArea

class ScenarioForm(FlaskForm):
    title = StringField(label='Title',
                        validators=[InputRequired(message='Title is required')])
    birthdate = DateField(label='Date of birth (MM-DD-YYYY)',
                          format='%m-%d-%Y',
                          validators=[InputRequired(message='Required')])
    s_birthdate = DateField(label='Date of birth(MM-DD-YYYY)',
                            format='%m-%d-%Y')

    current_income = IntegerField(label='Current income',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_current_income = IntegerField(label="Spouse's current income")

    savings_rate = DecimalField(label='Savings rate',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_savings_rate = DecimalField(label="Spouse's spouse's savings rate")

    ss_date = DateField(label='Date you will take Social Security (MM-DD-YYYY)',
                              format='%m-%d-%Y',
                              validators=[InputRequired(message='Required')])
    s_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY)',
                                format='%m-%d-%Y')

    ss_amount = IntegerField(label='SS amount',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_ss_amount = IntegerField(label="Spouse's SS amount")

    retirement_age = IntegerField(label='Retirement age',
                                  validators=[NumberRange(min=35, max=100,
                                                          message='Must be between 35 and 100')])
    s_retirement_age = IntegerField(label="Spouse's retirement age")

    ret_income = IntegerField(label='Retirement income',
                              validators=[InputRequired(message='Required(can be 0)')])
    s_ret_income = IntegerField(label="Spouse's retirement income")

    ret_job_ret_age = IntegerField(label='Age at which you will fully retire',
                                   validators=[InputRequired(message='Required')])
    s_ret_job_ret_age = IntegerField(label='Age at which your spouse will fully retire')

    lifespan_age = IntegerField(label='Expected lifespan in years',
                                validators=[InputRequired(message='Required(can be 0)')])
    s_lifespan_age = IntegerField(label="Spouse's expected lifespan in years")

    windfall_amount = IntegerField(label='Windfall amount',
                                   validators=[NumberRange(min=0, max=1000000000,
                                                           message='Windfall amount must be between 0 and 1,000,000,000')])
    windfall_age = IntegerField(label='Windfall age',
                                validators=[NumberRange(min=30, max=100,
                                                        message='Windfall amount must be between 30 and 100')])

    nestegg = IntegerField(label="Your investable savings",
                           validators=[InputRequired(message='Required(can be 0)')])
    ret_spend = IntegerField(label="Expected annual spending in retirement",
                             validators=[InputRequired(message='Required')])
    has_spouse = BooleanField(label='Married', default=True)

    investment = SelectField(label='Investment', coerce=int, validate_choice=False)

    submit = SubmitField('Save')
    submitrun = SubmitField('Save and Run')


class DisplaySimResultForm(FlaskForm):
    title = StringField()

    taf = StringField(widget=TextArea(), render_kw={'readonly': True, 'rows': 20})

    submit = SubmitField('Update scenario')
