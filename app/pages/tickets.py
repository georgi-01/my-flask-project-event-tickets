from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import AppError, NotFoundError, ValidationError
from app.formatting import count_label
from app.pages import bp
from app.services import cashdesks as cashdesk_service
from app.services import events as event_service
from app.services import tickets as ticket_service


def _form(data):
    def text(key):
        value = data.get(key, "")
        return "" if value is None else str(value)

    return {
        "event_id": text("event_id"),
        "cash_desk_id": text("cash_desk_id"),
        "ticket_type": data.get("ticket_type", ""),
        "seat_code": data.get("seat_code", ""),
        "buyer_name": data.get("buyer_name", ""),
        "status": data.get("status") or "sold",
    }


def _render_form(form, error, mode, ticket_id=None, status=400):
    return (
        render_template(
            "ticket_form.html",
            form=form,
            events=event_service.list_events({}),
            desks=cashdesk_service.list_cashdesks(),
            error=error,
            mode=mode,
            ticket_id=ticket_id,
        ),
        status,
    )


@bp.get("/tickets")
def ticket_list():
    tickets = ticket_service.list_tickets()
    return render_template(
        "ticket_list.html",
        tickets=tickets,
        count_text=count_label(len(tickets), "билет", "билета"),
    )


@bp.get("/tickets/new")
def ticket_new():
    return _render_form(_form({}), None, "create", status=200)


@bp.post("/tickets")
def ticket_create():
    form = request.form.to_dict()
    try:
        saved = ticket_service.create_ticket(form)
    except ValidationError as err:
        return _render_form(_form(form), err.message, "create")
    flash("Билетът е записан.", "success")
    return redirect(url_for("pages.ticket_detail", ticket_id=saved["id"]))


@bp.get("/tickets/<int:ticket_id>")
def ticket_detail(ticket_id):
    try:
        ticket = ticket_service.get_ticket(ticket_id)
    except NotFoundError:
        abort(404)
    return render_template("ticket_detail.html", ticket=ticket)


@bp.get("/tickets/<int:ticket_id>/edit")
def ticket_edit(ticket_id):
    try:
        ticket = ticket_service.get_ticket(ticket_id)
    except NotFoundError:
        abort(404)
    return _render_form(_form(ticket), None, "edit", ticket_id, status=200)


@bp.post("/tickets/<int:ticket_id>/edit")
def ticket_update(ticket_id):
    form = request.form.to_dict()
    try:
        ticket_service.update_ticket(ticket_id, form)
    except NotFoundError:
        abort(404)
    except ValidationError as err:
        return _render_form(_form(form), err.message, "edit", ticket_id)
    except AppError as err:
        return _render_form(_form(form), err.message, "edit", ticket_id, status=err.status)
    flash("Билетът е променен.", "success")
    return redirect(url_for("pages.ticket_detail", ticket_id=ticket_id))


@bp.post("/tickets/<int:ticket_id>/delete")
def ticket_delete(ticket_id):
    try:
        ticket_service.delete_ticket(ticket_id)
    except NotFoundError:
        abort(404)
    flash("Билетът е изтрит.", "success")
    return redirect(url_for("pages.ticket_list"))
