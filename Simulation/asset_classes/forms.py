from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField, DecimalField
from wtforms.validators import InputRequired



class AssetClassForm(FlaskForm):
    title = StringField(label='Name of asset class', validators=[InputRequired(message='Required')])
    avg_ret = DecimalField(label='Average annual return', places=5,
                           number_format="{:.2%}", validators=[InputRequired(message='Required')])
    std_dev = DecimalField(label='Risk (standard deviation)', places=5, number_format="{:.2%}", validators=[InputRequired(message='Required')])
    submit = SubmitField('Save Asset Class')


class AssetClassListForm(FlaskForm):
    nas = SubmitField('New Asset Class')
    home = SubmitField('Home')