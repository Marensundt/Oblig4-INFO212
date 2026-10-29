"""Admin blueprint: A1 food items, A2 images, A3 orders, A4 questions. Staff only (US-21)."""
from dataclasses import replace

from flask import (Blueprint, abort, current_app, flash, g, redirect, render_template, request, send_file,
                   session, url_for)
from wtforms import SelectChoice

from app.controllers.decorators import admin_required
from app.controllers.forms import (AnswerForm, FoodItemForm, ImageInstructionForm, ImageUploadForm, OrderFilterForm,
                                   OrderStatusForm, PaymentStatusForm)
from app.controllers.shop import picture_headers
from app.models.catalogue import delete_food_item, set_published
from app.models.entities import FoodItem
from app.models.enums import Allergen, DietaryLabel, OrderStatus, PaymentStatus
from app.models.errors import AlreadyAnswered, InvalidQuestion, InvalidStatusTransition, ItemInUse, NotFound
from app.models.images import ImageError, check_instruction, check_upload, extension_of
from app.models.questions import answer_question

bp = Blueprint("admin", __name__, url_prefix="/admin")


@bp.get("/")
@admin_required
def index():
    waiting = len(current_app.repos.orders.list(status=OrderStatus.SUBMITTED))
    unanswered = sum(not q.is_answered for q in current_app.repos.questions.list_all())
    return render_template("admin/index.html", orders_waiting=waiting, questions_unanswered=unanswered)


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


# --- A2 Images -----------------------------------------------------------------------------
# A new picture is "pending" until the admin saves it after the preview (OB4 A2).
PENDING_KEY = "pending_image"


def _pending_for(item_id):
    pending = session.get(PENDING_KEY)
    return pending if pending and pending.get("item_id") == item_id else None


def _set_pending(item_id, name, source):
    _drop_pending()
    session[PENDING_KEY] = {"item_id": item_id, "name": name, "source": source}


def _drop_pending():
    pending = session.pop(PENDING_KEY, None)
    if pending:
        current_app.images.discard_pending(pending["name"])


def _image_page(item, upload_form=None, instruction_form=None):
    return render_template(
        "admin/food/image.html", item=item, service_name=current_app.image_service.name,
        upload_form=upload_form or ImageUploadForm(), instruction_form=instruction_form or ImageInstructionForm(),
        can_modify=extension_of(item.image_filename) == "svg",
    )


@bp.get("/food/<int:item_id>/image")
@admin_required
def food_image(item_id):
    """US-04, US-05: upload a picture or write an instruction."""
    return _image_page(_get_item_or_404(item_id))


@bp.post("/food/<int:item_id>/image/upload")
@admin_required
def food_image_upload(item_id):
    item = _get_item_or_404(item_id)
    form = ImageUploadForm()
    if form.validate_on_submit():
        data = form.picture.data.read()
        try:
            ext = check_upload(form.picture.data.filename, data)
        except ImageError as error:
            form.picture.errors.append(str(error))
        else:
            _set_pending(item.id, current_app.images.add_pending(item.id, ext, data), "upload")
            return redirect(url_for("admin.food_image_preview", item_id=item.id))
    return _image_page(item, upload_form=form)


@bp.post("/food/<int:item_id>/image/generate")
@admin_required
def food_image_generate(item_id):
    item = _get_item_or_404(item_id)
    form = ImageInstructionForm()
    if form.validate_on_submit():
        try:
            instruction = check_instruction(form.instruction.data)
            current_svg = None
            if form.mode.data == "modify":
                if extension_of(item.image_filename) != "svg":
                    raise ImageError("Only SVG pictures can be modified. Create a new picture instead.")
                current_svg = (current_app.images.read(item.image_filename) or b"").decode("utf-8", "replace")
            svg = current_app.image_service.create_svg(item, instruction, current_svg)
        except ImageError as error:
            form.instruction.errors.append(str(error))
        else:
            name = current_app.images.add_pending(item.id, "svg", svg.encode("utf-8"))
            _set_pending(item.id, name, f"{current_app.image_service.name}: “{instruction}”")
            return redirect(url_for("admin.food_image_preview", item_id=item.id))
    return _image_page(item, instruction_form=form)


@bp.get("/food/<int:item_id>/image/preview")
@admin_required
def food_image_preview(item_id):
    """OB4 A2: the admin previews the result before it is saved."""
    item = _get_item_or_404(item_id)
    pending = _pending_for(item.id)
    if pending is None:
        flash("There is no new picture to preview. Upload or create one first.", "info")
        return redirect(url_for("admin.food_image", item_id=item.id))
    return render_template("admin/food/image_preview.html", item=item, pending=pending)


@bp.get("/food/<int:item_id>/image/pending")
@admin_required
def food_image_pending(item_id):
    pending = _pending_for(item_id)
    if pending is None:
        abort(404)
    try:
        path = current_app.images.pending_path(pending["name"])
    except ImageError:
        abort(404)
    return picture_headers(send_file(path, max_age=0))


@bp.post("/food/<int:item_id>/image/save")
@admin_required
def food_image_save(item_id):
    item = _get_item_or_404(item_id)
    pending = _pending_for(item.id)
    try:
        if pending is None:
            raise ImageError("There is no new picture to save. Upload or create one again.")
        filename = current_app.images.save_pending(pending["name"])
    except ImageError as error:
        flash(str(error), "error")
        return redirect(url_for("admin.food_image", item_id=item.id))
    session.pop(PENDING_KEY, None)
    old = item.image_filename
    current_app.repos.food_items.update(replace(item, image_filename=filename))
    current_app.images.delete(old)
    flash(f"The new picture of “{item.name}” was saved.", "success")
    return redirect(url_for("admin.food_image", item_id=item.id))


@bp.post("/food/<int:item_id>/image/discard")
@admin_required
def food_image_discard(item_id):
    item = _get_item_or_404(item_id)
    if _pending_for(item.id):
        _drop_pending()
    flash("The new picture was discarded. The item is unchanged.", "info")
    return redirect(url_for("admin.food_image", item_id=item.id))


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
                           status_form=_status_form(order), payment_form=payment_form,
                           questions=current_app.repos.questions.list_for_order(order.id))


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


# --- A4 Questions --------------------------------------------------------------------------

@bp.get("/questions")
@admin_required
def question_list():
    """US-20 AC1: all questions, unanswered first, each with its order and customer."""
    questions = current_app.repos.questions.list_all()
    orders = {order.id: order for order in current_app.repos.orders.list()}
    customers = {user.id: user for user in current_app.repos.users.list_customers()}
    return render_template("admin/questions/list.html", questions=questions, orders=orders, customers=customers)


@bp.post("/questions/<int:question_id>/answer")
@admin_required
def question_answer(question_id):
    """US-20 AC2, AC3: store the answer with the admin and the time; empty answers are rejected."""
    question = current_app.repos.questions.get(question_id)
    if question is None:
        abort(404)
    form = AnswerForm()
    if form.from_order.data:
        back = url_for("admin.order_detail", order_id=question.order_id) + "#questions"
    else:
        back = url_for("admin.question_list")
    try:
        if not form.validate_on_submit():
            raise InvalidQuestion("Write your answer first.")
        answer_question(current_app.repos, g.user, question_id, form.text.data)
    except (InvalidQuestion, AlreadyAnswered) as error:
        flash(f"Answer not saved. {error}", "error")
    else:
        flash("The answer has been sent. The customer sees it on the order page.", "success")
    return redirect(back)
