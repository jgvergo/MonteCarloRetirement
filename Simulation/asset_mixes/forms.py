from flask_wtf import FlaskForm
from wtforms import SubmitField, StringField
from wtforms.validators import InputRequired
from wtforms.widgets import TextArea


class AssetMixForm(FlaskForm):
    title = StringField(label='Name of asset mix', validators=[InputRequired(message='Required')])
    description = StringField(widget=TextArea(), render_kw={'rows': 5})
    add = SubmitField('+')
    submit = SubmitField('Save Asset Mix')
    delete = SubmitField('Delete Asset Mix')


class AssetMixListForm(FlaskForm):
    nam = SubmitField('New Asset Mix')
    home = SubmitField('Home')