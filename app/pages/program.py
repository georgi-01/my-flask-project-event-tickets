from flask import abort, flash, redirect, render_template, request, url_for

from app.errors import NotFoundError, ValidationError
from app.formatting import count_label
from app.pages import bp
from app.parsing import parse_bool
from app.services import cashdesks as cashdesk_service
from app.services import events as event_service
from app.services import tickets as ticket_service
from app.services import venues as venue_service


def _filters():
    raw = {
        "q": request.args.get("q", ""),
        "city": request.args.get("city", ""),
        "venue_type": request.args.get("venue_type", ""),
        "country": request.args.get("country", ""),
        "date": request.args.get("date", ""),
        "student": request.args.get("student", ""),
        "bottle": request.args.get("bottle", ""),
    }
    view = dict(raw)
    view["student"] = parse_bool(raw["student"])
    view["bottle"] = parse_bool(raw["bottle"])
    return raw, view


def _event_form(data):
    venue_id = data.get("venue_id", "")
    return {
        "venue_id": "" if venue_id in (None, "") else str(venue_id),
        "performer": data.get("performer", ""),
        "starts_input": data.get("starts_input") or data.get("starts_at") or "",
        "adult_price": data.get("adult_price", ""),
        "description": data.get("description", ""),
    }


def _buy_form(data=None):
    data = data or {}
    desk = data.get("cash_desk_id", "")
    return {
        "ticket_type": data.get("ticket_type", ""),
        "seats": data.get("seats", ""),
        "buyer_name": data.get("buyer_name", ""),
        "cash_desk_id": "" if desk in (None, "") else str(desk),
    }


@bp.get("/")
def home():
    raw, view = _filters()
    error = None
    try:
        events = event_service.list_events(raw)
    except ValidationError as err:
        events = []
        error = err.message
    filters_open = any(
        [view["city"], view["venue_type"], view["country"], view["date"], view["student"], view["bottle"]]
    )
    return render_template(
        "home.html",
        events=events,
        filters=view,
        filters_open=filters_open,
        cities=venue_service.list_cities(),
        countries=venue_service.list_countries(),
        error=error,
        count_text=count_label(len(events), "събитие", "събития"),
    )


@bp.get("/events/new")
def event_new():
    return render_template(
        "event_form.html",
        form=_event_form({}),
        venues=venue_service.list_venues(),
        error=None,
        mode="create",
    )


@bp.post("/events")
def event_create():
    form = request.form.to_dict()
    try:
        saved = event_service.create_event(form)
    except ValidationError as err:
        return (
            render_template(
                "event_form.html",
                form=_event_form(form),
                venues=venue_service.list_venues(),
                error=err.message,
                mode="create",
            ),
            400,
        )
    flash("Събитието е записано.", "success")
    return redirect(url_for("pages.event_detail", event_id=saved["id"]))


@bp.get("/events/<int:event_id>")
def event_detail(event_id):
    try:
        event = event_service.get_event(event_id)
    except NotFoundError:
        abort(404)
    return render_template(
        "event_detail.html",
        event=event,
        seat_rows=ticket_service.seat_map(event_id),
        desks=cashdesk_service.list_cashdesks(),
        error=None,
        form=_buy_form(),
    )


@bp.post("/events/<int:event_id>/buy")
def event_buy(event_id):
    form = request.form.to_dict()
    form["event_id"] = event_id
    try:
        ticket_service.purchase(event_id, form)
    except NotFoundError:
        abort(404)
    except ValidationError as err:
        return (
            render_template(
                "event_detail.html",
                event=event_service.get_event(event_id),
                seat_rows=ticket_service.seat_map(event_id),
                desks=cashdesk_service.list_cashdesks(),
                error=err.message,
                form=_buy_form(form),
            ),
            400,
        )
    except Exception as err:
        from app.errors import AppError

        if not isinstance(err, AppError):
            raise
        return (
            render_template(
                "event_detail.html",
                event=event_service.get_event(event_id),
                seat_rows=ticket_service.seat_map(event_id),
                desks=cashdesk_service.list_cashdesks(),
                error=err.message,
                form=_buy_form(form),
            ),
            err.status,
        )
    flash("Билетите са закупени.", "success")
    return redirect(url_for("pages.ticket_list"))


@bp.get("/events/<int:event_id>/edit")
def event_edit(event_id):
    try:
        event = event_service.get_event(event_id)
    except NotFoundError:
        abort(404)
    return render_template(
        "event_form.html",
        form=_event_form(event),
        venues=venue_service.list_venues(),
        error=None,
        mode="edit",
        event_id=event_id,
    )


@bp.post("/events/<int:event_id>/edit")
def event_update(event_id):
    form = request.form.to_dict()
    try:
        event_service.update_event(event_id, form)
    except NotFoundError:
        abort(404)
    except ValidationError as err:
        return (
            render_template(
                "event_form.html",
                form=_event_form(form),
                venues=venue_service.list_venues(),
                error=err.message,
                mode="edit",
                event_id=event_id,
            ),
            400,
        )
    flash("Събитието е променено.", "success")
    return redirect(url_for("pages.event_detail", event_id=event_id))


@bp.post("/events/<int:event_id>/delete")
def event_delete(event_id):
    try:
        event_service.delete_event(event_id)
    except NotFoundError:
        abort(404)
    flash("Събитието е изтрито.", "success")
    return redirect(url_for("pages.home"))
