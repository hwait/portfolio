from flask_wtf import FlaskForm
from wtforms import StringField,SelectField,HiddenField
from wtforms.validators import DataRequired

class AnalyticForm(FlaskForm):
    country = SelectField('country', coerce=str)
    keyword = SelectField('keyword', coerce=str)
    action = HiddenField('action')

class SearchForm(FlaskForm):
    keyword = StringField('keyword', validators=[DataRequired()])
    country = SelectField('country', choices=[('AUS', 'Australia'), ('CAN', 'Canada'), ('GB', 'Great Britain'), ('NZ', 'New Zealand'), ('POR', 'Portugal'), ('USCAL', 'USA / Caligornia'), ('USMIA', 'USA / Miami')])
    #country = SelectField('country', coerce=str)

class ListForm(FlaskForm):
    returntype = HiddenField('t', validators=[DataRequired()])
    ids = HiddenField('ids', validators=[DataRequired()])
