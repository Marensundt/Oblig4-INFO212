"""Admin blueprint: A1 food items, A2 images, A3 orders, A4 questions. Staff only (US-21)."""
from dataclasses import replace

from flask import Blueprint, abort, current_app, flash, redirect, render_template, request, url_for
from wtforms import SelectChoice

from app.controllers.decorators import admin_required
from app.controllers.forms import FoodItemForm
from app.models.catalogue import delete_food_item, set_published
from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel
from app.models.errors import ItemInUse, NotFound

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@admin_required
def index():
    return render_template("admin/index.html")


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
