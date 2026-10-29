"""Admin blueprint: A1 food items, A2 images, A3 orders, A4 questions. Staff only (US-21)."""
from dataclasses import replace

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from wtforms import SelectChoice

from app.controllers.decorators import admin_required
from app.controllers.forms import FoodItemForm, OrderFilterForm, OrderStatusForm, PaymentStatusForm
from app.models.catalogue import delete_food_item, set_published
from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel, OrderStatus, PaymentStatus
from app.models.errors import InvalidStatusTransition, ItemInUse, NotFound

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@admin_required
def index():
    waiting = len(current_app.repos.orders.list(status=OrderStatus.SUBMITTED))
    return render_template("admin/index.html", orders_waiting=waiting)


# --- A1 Food items -------------------------------------------------------------------------

def _food_form(item=None):
    form = FoodItemForm(obj=item)
    form.category_ids.choices = [SelectChoice(c.id, c.name) for c in current_app.repos.categories.list_all()]
    return form


def _get_item_or_404(item_id):
    item = current_app.repos.food_items.get(item_id)
    if item is None:
        abort(404)
    return item


def _fields_from(form):
    return dict(
        name=form.name.data.strip(),
        description=(form.description.data or "").strip(),
        price_nok=form.price_nok.data,
        min_order_qty=form.min_order_qty.data,
        category_ids=list(form.category_ids.data),
        allergens={Allergen(a) for a in form.allergens.data or []},
        dietary_labels={DietaryLabel(d) for d in form.dietary_labels.data or []},
        published=form.published.data,
    )


@bp.get("/food")
@admin_required
def food_list():
    categories = {c.id: c.name for c in current_app.repos.categories.list_all()}
    return render_template("admin/food/list.html", items=current_app.repos.food_items.list_all(),
                           categories=categories)


@bp.route("/food/new", methods=["GET", "POST"])
@admin_required
def food_new():
    form = _food_form()
    if form.validate_on_submit():
        item = current_app.repos.food_items.add(FoodItem(**_fields_from(form)))
        flash(f"“{item.name}” was added.", "success")
        return redirect(url_for("admin.food_list"))
    return render_template("admin/food/form.html", form=form, item=None)


@bp.route("/food/<int:item_id>/edit", methods=["GET", "POST"])
@admin_required
def food_edit(item_id):
    item = _get_item_or_404(item_id)
    form = _food_form(item)
    if form.validate_on_submit():
        # The picture (A2, phase 9) is not part of this form and is kept unchanged.
        updated = current_app.repos.food_items.update(replace(item, **_fields_from(form)))
        flash(f"“{updated.name}” was saved.", "success")
        return redirect(url_for("admin.food_list"))
    return render_template("admin/food/form.html", form=form, item=item)


@bp.post("/food/<int:item_id>/publish")
@admin_required
def food_publish(item_id):
    published = request.form.get("published") == "1"
    try:
        item = set_published(current_app.repos, item_id, published)
    except NotFound:
        abort(404)
    flash(f"“{item.name}” is now {'published' if published else 'hidden from the menu'}.", "success")
    return redirect(url_for("admin.food_list"))


@bp.post("/food/<int:item_id>/delete")
@admin_required
def food_delete(item_id):
    item = _get_item_or_404(item_id)
    try:
        delete_food_item(current_app.repos, item_id)
    except ItemInUse:
        flash(f"“{item.name}” is part of existing orders and cannot be deleted. "
              "Unpublish it instead to hide it from the menu.", "error")
    else:
        flash(f"“{item.name}” was deleted.", "success")
    return redirect(url_for("admin.food_list"))


# --- A3 Orders -----------------------------------------------------------------------------

def _get_order_or_404(order_id):
    order = current_app.repos.orders.get(order_id)
    if order is None:
        abort(404)
    return order


def _status_form(order):
    form = OrderStatusForm()
    form.status.choices = [SelectChoice(s.value, s.label.capitalize()) for s in order.status.next_statuses]
    return form


@bp.get("/orders")
@admin_required
def order_list():
    """US-14: all orders sorted by event date, filtered by status and event-date range."""
    form = OrderFilterForm(request.args)
    filters = {}
    if form.validate():
        filters = dict(status=form.status.data or None, date_from=form.date_from.data, date_to=form.date_to.data)
    orders = current_app.repos.orders.list(**filters)
    customers = {user.id: user for user in current_app.repos.users.list_customers()}
    return render_template("admin/orders/list.html", form=form, orders=orders, customers=customers,
                           filtered=any(filters.values()))


@bp.get("/orders/<int:order_id>")
@admin_required
def order_detail(order_id):
    """US-15 AC1: everything about the order, allergies highlighted; status and payment forms."""
    order = _get_order_or_404(order_id)
    payment_form = PaymentStatusForm(payment_status=order.payment_status.value)
    return render_template("admin/orders/detail.html", order=order,
                           customer=current_app.repos.users.get(order.customer_id),
                           status_form=_status_form(order), payment_form=payment_form)


@bp.post("/orders/<int:order_id>/status")
@admin_required
def order_status(order_id):
    """US-15 AC2–AC4: only transitions allowed by OrderStatus.can_change_to are saved."""
    order = _get_order_or_404(order_id)
    form = _status_form(order)
    if not form.validate_on_submit():
        # A status that is not offered is an illegal transition (e.g. delivered → submitted)
        flash(f"The order status cannot change from {order.status.label} to that status.", "error")
        return redirect(url_for("admin.order_detail", order_id=order_id))
    try:
        order = current_app.repos.orders.update_status(order_id, form.status.data)
    except InvalidStatusTransition as error:
        flash(f"{error}.", "error")
    else:
        flash(f"Order {order.order_number} is now {order.status.label}.", "success")
    return redirect(url_for("admin.order_detail", order_id=order_id))


@bp.post("/orders/<int:order_id>/payment")
@admin_required
def order_payment(order_id):
    """US-16 AC2: payment status is set manually (no payment solution, OB4 C3)."""
    order = _get_order_or_404(order_id)
    form = PaymentStatusForm()
    if form.validate_on_submit():
        order = current_app.repos.orders.update_payment_status(order_id, PaymentStatus(form.payment_status.data))
        flash(f"Payment status of order {order.order_number} is now {order.payment_status.label}.", "success")
    else:
        flash("Choose a valid payment status.", "error")
    return redirect(url_for("admin.order_detail", order_id=order_id))
