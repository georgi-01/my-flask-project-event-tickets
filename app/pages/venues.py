from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import NotFoundError, ValidationError
from app.pages import bp
from app.parsing import parse_bool
from app.services import events as event_service
from app.services import venues as venue_service


def _form(data):
    return {
        "name": data.get("name", ""),
        "venue_type": data.get("venue_type", ""),
        "city": data.get("city", ""),
        "address": data.get("address", ""),
        "country": data.get("country", ""),
        "description": data.get("description", ""),
        "free_student_entry": parse_bool(data.get("free_student_entry")),
        "bottle_discount": parse_bool(data.get("bottle_discount")),
    }


def _posted():
    form = request.form.to_dict()
    form["free_student_entry"] = request.form.get("free_student_entry")
    form["bottle_discount"] = request.form.get("bottle_discount")
    return form


@bp.get("/venues")
def venue_list():
    return render_template("venue_list.html", venues=venue_service.list_venues())


@bp.get("/venues/new")
def venue_new():
    return render_template("venue_form.html", form=_form({}), error=None, mode="create")


@bp.post("/venues")
def venue_create():
    form = _posted()
    try:
        saved = venue_service.create_venue(form)
    except ValidationError as err:
        return render_template("venue_form.html", form=_form(form), error=err.message, mode="create"), 400
    flash("Мястото е записано.", "success")
    return redirect(url_for("pages.venue_detail", venue_id=saved["id"]))


@bp.get("/venues/<int:venue_id>")
def venue_detail(venue_id):
    try:
        venue = venue_service.get_venue(venue_id)
        events = event_service.list_for_venue(venue_id)
    except NotFoundError:
        abort(404)
    return render_template("venue_detail.html", venue=venue, events=events)


@bp.get("/venues/<int:venue_id>/edit")
def venue_edit(venue_id):
    try:
        venue = venue_service.get_venue(venue_id)
    except NotFoundError:
        abort(404)
    return render_template(
        "venue_form.html",
        form=_form(venue),
        error=None,
        mode="edit",
        venue_id=venue_id,
    )


@bp.post("/venues/<int:venue_id>/edit")
def venue_update(venue_id):
    form = _posted()
    try:
        venue_service.update_venue(venue_id, form)
    except NotFoundError:
        abort(404)
    except ValidationError as err:
        return (
            render_template(
                "venue_form.html",
                form=_form(form),
                error=err.message,
                mode="edit",
                venue_id=venue_id,
            ),
            400,
        )
    flash("Мястото е променено.", "success")
    return redirect(url_for("pages.venue_detail", venue_id=venue_id))


@bp.post("/venues/<int:venue_id>/delete")
def venue_delete(venue_id):
    try:
        venue_service.delete_venue(venue_id)
    except NotFoundError:
        abort(404)
    flash("Мястото е изтрито.", "success")
    return redirect(url_for("pages.venue_list"))
