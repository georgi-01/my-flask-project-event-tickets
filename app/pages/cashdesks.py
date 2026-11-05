from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import AppError, NotFoundError, ValidationError
from app.pages import bp
from app.services import cashdesks as cashdesk_service
from app.services import venues as venue_service


def _form(data):
    venue_id = data.get("venue_id", "")
    return {
        "name": data.get("name", ""),
        "city": data.get("city", ""),
        "address": data.get("address", ""),
        "operator_name": data.get("operator_name", ""),
        "venue_id": "" if venue_id in (None, "") else str(venue_id),
    }


def _render(form, error, mode, desk_id=None, status=400):
    return (
        render_template(
            "desk_form.html",
            form=form,
            venues=venue_service.list_venues(),
            error=error,
            mode=mode,
            desk_id=desk_id,
        ),
        status,
    )


@bp.get("/cash-desks")
def desk_list():
    return render_template("desk_list.html", desks=cashdesk_service.list_cashdesks())


@bp.get("/cash-desks/new")
def desk_new():
    return _render(_form({}), None, "create", status=200)


@bp.post("/cash-desks")
def desk_create():
    form = request.form.to_dict()
    try:
        saved = cashdesk_service.create_cashdesk(form)
    except ValidationError as err:
        return _render(_form(form), err.message, "create")
    flash("Касата е записана.", "success")
    return redirect(url_for("pages.desk_detail", desk_id=saved["id"]))


@bp.get("/cash-desks/<int:desk_id>")
def desk_detail(desk_id):
    try:
        desk = cashdesk_service.get_cashdesk(desk_id)
    except NotFoundError:
        abort(404)
    return render_template("desk_detail.html", desk=desk)


@bp.get("/cash-desks/<int:desk_id>/edit")
def desk_edit(desk_id):
    try:
        desk = cashdesk_service.get_cashdesk(desk_id)
    except NotFoundError:
        abort(404)
    return _render(_form(desk), None, "edit", desk_id, status=200)


@bp.post("/cash-desks/<int:desk_id>/edit")
def desk_update(desk_id):
    form = request.form.to_dict()
    try:
        cashdesk_service.update_cashdesk(desk_id, form)
    except NotFoundError:
        abort(404)
    except ValidationError as err:
        return _render(_form(form), err.message, "edit", desk_id)
    flash("Касата е променена.", "success")
    return redirect(url_for("pages.desk_detail", desk_id=desk_id))


@bp.post("/cash-desks/<int:desk_id>/delete")
def desk_delete(desk_id):
    try:
        cashdesk_service.delete_cashdesk(desk_id)
    except NotFoundError:
        abort(404)
    except AppError as err:
        flash(err.message, "error")
        return redirect(url_for("pages.desk_detail", desk_id=desk_id))
    flash("Касата е изтрита.", "success")
    return redirect(url_for("pages.desk_list"))
