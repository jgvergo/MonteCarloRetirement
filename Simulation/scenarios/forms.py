from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, DateField
from wtforms.validators import InputRequired, NumberRange
from flask_wtf.file import FileField, FileAllowed

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

    start_ss_date = DateField(label='Date you will take Social Security (MM-DD-YYYY)',
                              format='%m-%d-%Y',
                              validators=[InputRequired(message='Required')])
    s_start_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY)',
                                format='%m-%d-%Y')

    full_ss_amount = IntegerField(label='SS amount',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_full_ss_amount = IntegerField(label="Spouse's full SS amount")

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
    drawdown = IntegerField(label="Expected annual spending in retirement",
                            validators=[InputRequired(message='Required')])
    has_spouse = BooleanField(label='Married', default=True)

    submit = SubmitField('Save')
    submitrun = SubmitField('Save and Run')


class DisplaySimResultForm(FlaskForm):
    title = StringField()

    mode = IntegerField(label="Mode", render_kw={'readonly': True})
    median = IntegerField(label="Median", render_kw={'readonly': True})
    mean = IntegerField(label="Mean", render_kw={'readonly': True})

    birthdate = DateField(label='Date of birth (MM-DD-YYYY)',
                          format='%m-%d-%Y', render_kw={'readonly': True})
    s_birthdate = DateField(label='Date of birth(MM-DD-YYYY)',
                            format='%m-%d-%Y', render_kw={'readonly': True})

    current_income = IntegerField(label='Current income',
                                  render_kw={'readonly': True})
    s_current_income = IntegerField(label="Spouse's current income", render_kw={'readonly': True})

    start_ss_date = DateField(label='Date you will take Social Security (MM-DD-YYYY)',
                              format='%m-%d-%Y',
                              render_kw = {'readonly': True})
    s_start_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY)',
                                format='%m-%d-%Y', render_kw={'readonly': True})

    full_ss_amount = IntegerField(label='SS amount',
                                  render_kw={'readonly': True})
    s_full_ss_amount = IntegerField(label="Spouse's full SS amount", render_kw={'readonly': True})

    retirement_age = IntegerField(label='Retirement age', render_kw={'readonly': True})
    s_retirement_age = IntegerField(label="Spouse's retirement age", render_kw={'readonly': True})

    ret_income = IntegerField(label='Retirement income', render_kw={'readonly': True})
    s_ret_income = IntegerField(label="Spouse's retirement income", render_kw={'readonly': True})

    ret_job_ret_age = IntegerField(label='Age at which you will fully retire', render_kw={'readonly': True})
    s_ret_job_ret_age = IntegerField(label='Age at which your spouse will fully retire', render_kw={'readonly': True})

    lifespan_age = IntegerField(label='Expected lifespan in years', render_kw={'readonly': True})
    s_lifespan_age = IntegerField(label="Spouse's expected lifespan in years", render_kw={'readonly': True})

    windfall_amount = IntegerField(label='Windfall amount', render_kw={'readonly': True})
    windfall_age = IntegerField(label='Windfall age', render_kw={'readonly': True})

    nestegg = IntegerField(label="Your investable savings", render_kw={'readonly': True})
    drawdown = IntegerField(label="Expected annual spending in retirement", render_kw={'readonly': True})
    has_spouse = BooleanField(label='Married', default=True, render_kw={'readonly': True})

    submit = SubmitField('Update scenario')
