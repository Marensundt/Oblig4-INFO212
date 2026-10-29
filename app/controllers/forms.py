"""WTForms form classes (server-side validation + CSRF token)."""
from flask_wtf import FlaskForm
from wtforms import (
    BooleanField,
    DateField,
    FieldList,
    Form,
    FormField,
    SelectChoice,
    SelectField,
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
from app.models.enums import Allergen, DietaryLabel, OrderStatus, PaymentStatus
from app.models.ordering import MAX_GUEST_GROUPS
from app.models.questions import MAX_TEXT_LENGTH

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


class CartQuantityForm(FlaskForm):
    """Add to cart (menu card) or change a cart line (C2). Quantity rules live in app/models/cart.py."""

    item_id = IntegerField(validators=[InputRequired()])
    quantity = IntegerField("Portions", validators=[InputRequired("Enter the number of portions.")])


class GuestGroupForm(Form):
    """One guest group (C3). Deliberately no field for a guest's name (GDPR; US-13 AC3).

    A plain Form, not FlaskForm: the CSRF token belongs to the outer CheckoutForm.
    """

    label = StringField("Group", validators=[DataRequired("Name the group, e.g. “Adults”."), Length(max=60)])
    count = IntegerField("Guests in group", validators=[InputRequired("Enter the number of guests."),
                                                        NumberRange(min=1, message="At least 1 guest.")])
    allergies = MultiCheckboxField("Allergies", choices=[SelectChoice(a.value, a.label) for a in Allergen])
    dietary_notes = TextAreaField("Dietary notes", validators=[Optional(), Length(max=300)])


class CheckoutForm(FlaskForm):
    """C3 order form. Order rules (future date, group counts) are checked in app/models/ordering.py."""

    event_date = DateField("Event date", validators=[InputRequired("Choose the date of the event.")])
    guest_count = IntegerField("Number of guests",
                               validators=[InputRequired("Enter the number of guests."),
                                           NumberRange(min=1, message="The number of guests must be at least 1.")])
    delivery_address = TextAreaField("Delivery address",
                                     validators=[DataRequired("Enter a delivery address."), Length(max=300)])
    guest_groups = FieldList(FormField(GuestGroupForm), min_entries=1, max_entries=MAX_GUEST_GROUPS)
    add_group = SubmitField("Add another guest group")  # works without JavaScript
    submit = SubmitField("Send order")


class OrderFilterForm(FlaskForm):
    """A3 list filter, sent as GET query parameters (no CSRF token needed: it changes nothing)."""

    class Meta:
        csrf = False

    status = SelectField("Status", default="", choices=[SelectChoice("", "All statuses")]
                         + [SelectChoice(s.value, s.label.capitalize()) for s in OrderStatus])
    date_from = DateField("Event date from", validators=[Optional()])
    date_to = DateField("Event date to", validators=[Optional()])

    def validate_date_to(self, field):
        if field.data and self.date_from.data and field.data < self.date_from.data:
            raise ValidationError("“To” must be on or after “from”.")


class OrderStatusForm(FlaskForm):
    """Choices are the allowed next statuses, set by the controller from OrderStatus.next_statuses."""

    status = SelectField("New order status", validators=[DataRequired()])
    submit = SubmitField("Change status")


class PaymentStatusForm(FlaskForm):
    payment_status = SelectField("Payment status",
                                 choices=[SelectChoice(p.value, p.label.capitalize()) for p in PaymentStatus])
    submit = SubmitField("Save payment status")


class QuestionForm(FlaskForm):
    """C5. Length and empty-text rules live in app/models/questions.py."""

    text = TextAreaField("Your question", validators=[DataRequired("Write your question first.")],
                         render_kw={"maxlength": MAX_TEXT_LENGTH})
    submit = SubmitField("Send question")


class AnswerForm(FlaskForm):
    """A4. `from_order` sends the admin back to the order page instead of the question list."""

    text = TextAreaField("Answer", validators=[DataRequired("Write your answer first.")],
                         render_kw={"maxlength": MAX_TEXT_LENGTH})
    from_order = HiddenField()
    submit = SubmitField("Send answer")
