from flask_wtf import FlaskForm
from flask_wtf.file import FileField, FileRequired, FileAllowed
from wtforms import StringField, SubmitField
from wtforms.validators import DataRequired

class UploadForm(FlaskForm):
    company_name = StringField('Company Name', validators=[DataRequired()])
    report_file = FileField('Annual Report (PDF)', validators=[
        FileRequired(),
        FileAllowed(['pdf'], 'PDF files only!')
    ])
    submit = SubmitField('Upload')
