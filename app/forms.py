import sqlalchemy as sa
from flask_wtf import FlaskForm
from flask_babel import lazy_gettext as _l
from wtforms import StringField, PasswordField, BooleanField, SubmitField, TextAreaField
from wtforms.validators import DataRequired, Email, EqualTo, Length, ValidationError
from app import db
from app.models import User


class LoginForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    remember_me = BooleanField(_l('Remember Me'))
    submit = SubmitField(_l('Sign In'))


class RegistrationForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    password = PasswordField(_l('Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Confirm Password'),
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Create Account'))

    def validate_username(self, username):
        usr = db.session.scalar(
            sa.select(User).where(User.username == username.data))
        if usr is not None:
            raise ValidationError(_l('That username is already taken.'))

    def validate_email(self, email):
        usr = db.session.scalar(
            sa.select(User).where(User.email == email.data))
        if usr is not None:
            raise ValidationError(_l('That email address is already registered.'))


class EditProfileForm(FlaskForm):
    username = StringField(_l('Username'), validators=[DataRequired()])
    about_me = TextAreaField(_l('About Me'), validators=[Length(min=0, max=140)])
    submit = SubmitField(_l('Save Changes'))

    def __init__(self, original_username, *args, **kwargs):
        super().__init__(*args, **kwargs)
        self.original_username = original_username

    def validate_username(self, username):
        if username.data != self.original_username:
            usr = db.session.scalar(
                sa.select(User).where(User.username == username.data))
            if usr is not None:
                raise ValidationError(_l('That username is already taken.'))


class EmptyForm(FlaskForm):
    submit = SubmitField(_l('Submit'))


class PostForm(FlaskForm):
    post = TextAreaField(_l('Say something'),
                         validators=[DataRequired(), Length(min=1, max=140)])
    submit = SubmitField(_l('Post'))


class ResetPasswordRequestForm(FlaskForm):
    email = StringField(_l('Email'), validators=[DataRequired(), Email()])
    submit = SubmitField(_l('Send Reset Link'))


class ResetPasswordForm(FlaskForm):
    password = PasswordField(_l('New Password'), validators=[DataRequired()])
    password2 = PasswordField(_l('Confirm Password'),
                              validators=[DataRequired(), EqualTo('password')])
    submit = SubmitField(_l('Reset Password'))
