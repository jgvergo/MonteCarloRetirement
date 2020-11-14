from flask_wtf import FlaskForm
from wtforms import StringField, SubmitField, DecimalField, RadioField
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
    submit = SubmitField('Save')


class DisplaySimResultForm(FlaskForm):
    title = StringField(label='Scenario title',
                        validators=[InputRequired(message='Title is required')])
    submit = SubmitField('Home')