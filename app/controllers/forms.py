"""WTForms form classes (server-side validation + CSRF token)."""
from flask_wtf import FlaskForm
from wtforms import EmailField, HiddenField, PasswordField, StringField, SubmitField, TelField
from wtforms.validators import DataRequired, EqualTo, Length, Optional, Regexp

from app.models.accounts import MIN_PASSWORD_LENGTH

# Simple format check; full e-mail validation would need an extra package.
EMAIL_FORMAT = Regexp(r"^[^@\s]+@[^@\s]+\.[^@\s]+$", message="Enter a valid e-mail address.")


class LoginForm(FlaskForm):
    email = EmailField("E-mail", validators=[DataRequired(), EMAIL_FORMAT])
    password = PasswordField("Password", validators=[DataRequired()])
    next = HiddenField()
    submit = SubmitField("Log in")


class RegisterForm(FlaskForm):
    name = StringField("Name", validators=[DataRequired(), Length(max=100)])
    email = EmailField("E-mail", validators=[DataRequired(), EMAIL_FORMAT, Length(max=254)])
    phone = TelField("Phone (optional)", validators=[Optional(), Length(max=30)])
    password = PasswordField(
        "Password",
        validators=[DataRequired(), Length(min=MIN_PASSWORD_LENGTH,
                                           message=f"Use at least {MIN_PASSWORD_LENGTH} characters.")],
    )
    confirm = PasswordField(
        "Repeat password", validators=[DataRequired(), EqualTo("password", message="Passwords do not match.")]
    )
    next = HiddenField()
    submit = SubmitField("Create account")


class LogoutForm(FlaskForm):
    submit = SubmitField("Log out")
