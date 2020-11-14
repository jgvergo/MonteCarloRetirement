from flask_wtf import FlaskForm
from wtforms import SubmitField, BooleanField, DateField, HiddenField, IntegerField, RadioField
from wtforms.validators import InputRequired


class UserDataForm(FlaskForm):
    title = HiddenField(label='Please enter all data on this page. They are required.')
    birthdate = DateField(label='Birthday(MM-DD-YYYY):', format='%m-%d-%Y',
                          validators=[InputRequired(message='Required')])
    current_income = IntegerField(label='Current Income')
    lifespan_age = IntegerField(label='Expected age at death')
    full_ss_date = DateField(label='Date you entitled to full Social Security(MM-DD-YYYY):', format='%m-%d-%Y',
                          validators=[InputRequired(message='Required')])
    full_ss_amount = IntegerField(label='Your expected Social Security if take at your full retirement age')
    nestegg = IntegerField(label='Current Nest Egg')
    drawdown = IntegerField(label='Annual expenditures in retirement')

    # Information for spouse
    has_spouse = BooleanField(label='Married?')
    s_birthdate = DateField(label="Spouse's Birthday(MM-DD-YYYY):", format='%m-%d-%Y',
                            validators=[InputRequired(message='Required')])
    s_current_income = IntegerField(label="Spouse's Current Income")
    s_lifespan_age = IntegerField(label="Spouse's expected age at death")
    s_full_ss_date = DateField(label="Spouse's date he/she is entitled to full social security(MM-DD-YYYY):",
                               format='%m-%d-%Y', validators=[InputRequired(message='Required')])
    s_full_ss_amount = IntegerField(label='Your spouses expected Social Security if taken at his/her full retirement age')

    submit = SubmitField('Save it')