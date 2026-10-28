"""WTForms form classes (server-side validation + CSRF token)."""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    SelectChoice,
    EmailField,
    HiddenField,
    IntegerField,
    PasswordField,
    SelectMultipleField,
    StringField,
    SubmitField,
    TelField,
    TextAreaField,
)
from wtforms.validators import DataRequired, EqualTo, InputRequired, Length, NumberRange, Optional, Regexp, ValidationError
from wtforms.widgets import CheckboxInput, ListWidget

from app.models.accounts import MIN_PASSWORD_LENGTH
from app.models.enums import Allergen, DietaryLabel

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


class MultiCheckboxField(SelectMultipleField):
    widget = ListWidget(prefix_label=False)
    option_widget = CheckboxInput()


class FoodItemForm(FlaskForm):
    """All A1 fields. Category choices are set by the controller from the repository."""

    name = StringField("Name", validators=[DataRequired(), Length(max=120)])
    description = TextAreaField("Description", validators=[Optional(), Length(max=1000)])
    price_nok = IntegerField(
        "Price per portion (NOK)",
        validators=[InputRequired("Enter a price."), NumberRange(min=1, message="Price must be at least 1 NOK.")],
    )
    min_order_qty = IntegerField(
        "Minimum order (portions)",
        validators=[InputRequired("Enter a minimum order."),
                    NumberRange(min=1, message="Minimum order must be at least 1.")],
    )
    category_ids = MultiCheckboxField("Event categories", coerce=int)
    allergens = MultiCheckboxField("Allergens", choices=[SelectChoice(a.value, a.label) for a in Allergen])
    dietary_labels = MultiCheckboxField("Dietary labels", choices=[SelectChoice(d.value, d.label) for d in DietaryLabel])
    published = BooleanField("Published (shown on the customer menu)")
    submit = SubmitField("Save")

    def validate_category_ids(self, field):
        # DV-10 (ASSUMPTION): every item needs a category so it appears in the menu by event (C1)
        if not field.data:
            raise ValidationError("Choose at least one event category.")
