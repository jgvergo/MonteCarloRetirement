from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, BooleanField, IntegerField, DateField
from wtforms.validators import InputRequired, NumberRange, AnyOf


class ScenarioForm(FlaskForm):
    title = StringField(label='Title',
                        validators=[InputRequired(message='Title is required')])
    birthdate = DateField(label='Date of birth(MM-DD-YYYY):',
                          format='%m-%d-%Y',
                          validators=[InputRequired(message='Required')])
    s_birthdate = DateField(label='Date of birth(MM-DD-YYYY):',
                            format='%m-%d-%Y',
                            validators=[InputRequired(message='Required')])

    current_income = IntegerField(label='Current income:',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_current_income = IntegerField(label="Spouse's current income:",
                                    validators=[InputRequired(message='Required(can be 0)')])

    start_ss_date = DateField(label='Date you will take Social Security(MM-DD-YYYY):',
                              format='%m-%d-%Y',
                              validators = [InputRequired(message='Required')])
    s_start_ss_date = DateField(label='Date your spouse will take Social Security(MM-DD-YYYY):',
                                format='%m-%d-%Y',
                                validators = [InputRequired(message='Required')])

    full_ss_amount = IntegerField(label='Full SS amount:',
                                  validators=[InputRequired(message='Required(can be 0)')])
    s_full_ss_amount = IntegerField(label="Spouse's full SS amount:",
                                    validators=[InputRequired(message='Required(can be 0)')])

    retirement_age = IntegerField(label='Retirement age:',
                                  validators=[NumberRange(min=35, max=100,
                                  message='Retirement age must be between 35 and 100')])
    s_retirement_age = IntegerField(label="Spouse's retirement age:",
                                    validators=[NumberRange(min=35, max=100,
                                    message="Spouse's retirement age must be between 35 and 100")])

    ret_income = IntegerField(label='Retirement income:',
                              validators=[InputRequired(message='Required(can be 0)')])
    s_ret_income = IntegerField(label="Spouse's retirement income:",
                              validators=[InputRequired(message='Required(can be 0)')])

    ret_job_ret_age = IntegerField(label='Age at which you will fully retire:',
                                   validators = [InputRequired(message='Required')])
    s_ret_job_ret_age = IntegerField(label='Age at which your spouse will fully retire:',
                                     validators = [InputRequired(message='Required')])

    lifespan_age = IntegerField(label='Expected lifespan in years:',
                                validators=[InputRequired(message='Required(can be 0)')])
    s_lifespan_age = IntegerField(label="Spouse's expected lifespan in years",
                                  validators=[InputRequired(message='Required(can be 0)')])

    windfall_amount = IntegerField(label='Windfall amount:',
                                   validators=[NumberRange(min=0, max=1000000000,
                                   message='Windfall amount must be between 0 and 1,000,000,000')])
    windfall_age = IntegerField(label='Windfall age:',
                                validators=[NumberRange(min = 30, max=100,
                                message='Windfall amount must be between 30 and 100')])

    nestegg = IntegerField(label="Your investable savings",
                           validators=[InputRequired(message='Required(can be 0)')])
    drawdown = IntegerField(label="Expected annual spending in retirement",
                            validators=[InputRequired(message='Required')])
    has_spouse = BooleanField(label='Spouse', default=True)

    submit = SubmitField('Save')
    submitrun = SubmitField('Save and Run')
    cancel = SubmitField('Cancel')


class DisplaySimResultForm(FlaskForm):
    title = StringField(label='Scenario title',
                        validators=[InputRequired(message='Title is required')])
    submit = SubmitField('Home')

