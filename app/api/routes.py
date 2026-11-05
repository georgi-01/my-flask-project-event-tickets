from functools import wraps

from flask import jsonify, request

from app.api import bp
from app.errors import AppError, ValidationError
from app.services import activity as activity_service
from app.services import cashdesks as cashdesk_service
from app.services import events as event_service
from app.services import tickets as ticket_service
from app.services import venues as venue_service


def api(fn):
    @wraps(fn)
    def wrapper(*args, **kwargs):
        try:
            result = fn(*args, **kwargs)
        except AppError as err:
            return jsonify({"error": err.message}), err.status
        if result is None:
            return "", 204
        if isinstance(result, tuple):
            body, status = result
            return jsonify(body), status
        return jsonify(result)

    return wrapper


def body():
    data = request.get_json(silent=True)
    if not isinstance(data, dict):
        raise ValidationError("Очаква се JSON обект.")
    return data


def event_filters():
    return {
        "q": request.args.get("q", ""),
        "city": request.args.get("city", ""),
        "venue_type": request.args.get("venue_type", ""),
        "country": request.args.get("country", ""),
        "date": request.args.get("date", ""),
        "student": request.args.get("student", ""),
        "bottle": request.args.get("bottle", ""),
    }


@bp.get("/venues")
@api
def list_venues():
    return venue_service.list_venues()


@bp.post("/venues")
@api
def create_venue():
    return venue_service.create_venue(body()), 201


@bp.get("/venues/<int:venue_id>")
@api
def get_venue(venue_id):
    return venue_service.get_venue(venue_id)


@bp.put("/venues/<int:venue_id>")
@api
def update_venue(venue_id):
    return venue_service.update_venue(venue_id, body())


@bp.delete("/venues/<int:venue_id>")
@api
def delete_venue(venue_id):
    venue_service.delete_venue(venue_id)
    return None


@bp.get("/events")
@api
def list_events():
    return event_service.list_events(event_filters())


@bp.post("/events")
@api
def create_event():
    return event_service.create_event(body()), 201


@bp.get("/events/<int:event_id>")
@api
def get_event(event_id):
    return event_service.get_event(event_id)


@bp.put("/events/<int:event_id>")
@api
def update_event(event_id):
    return event_service.update_event(event_id, body())


@bp.delete("/events/<int:event_id>")
@api
def delete_event(event_id):
    event_service.delete_event(event_id)
    return None


@bp.get("/tickets")
@api
def list_tickets():
    return ticket_service.list_tickets()


@bp.post("/tickets")
@api
def create_ticket():
    return ticket_service.create_ticket(body()), 201


@bp.get("/tickets/<int:ticket_id>")
@api
def get_ticket(ticket_id):
    return ticket_service.get_ticket(ticket_id)


@bp.put("/tickets/<int:ticket_id>")
@api
def update_ticket(ticket_id):
    return ticket_service.update_ticket(ticket_id, body())


@bp.delete("/tickets/<int:ticket_id>")
@api
def delete_ticket(ticket_id):
    ticket_service.delete_ticket(ticket_id)
    return None


@bp.get("/cash-desks")
@api
def list_cashdesks():
    return cashdesk_service.list_cashdesks()


@bp.post("/cash-desks")
@api
def create_cashdesk():
    return cashdesk_service.create_cashdesk(body()), 201


@bp.get("/cash-desks/<int:desk_id>")
@api
def get_cashdesk(desk_id):
    return cashdesk_service.get_cashdesk(desk_id)


@bp.put("/cash-desks/<int:desk_id>")
@api
def update_cashdesk(desk_id):
    return cashdesk_service.update_cashdesk(desk_id, body())


@bp.delete("/cash-desks/<int:desk_id>")
@api
def delete_cashdesk(desk_id):
    cashdesk_service.delete_cashdesk(desk_id)
    return None


@bp.get("/activity")
@api
def list_activity():
    return activity_service.list_activity()


@bp.get("/activity/<int:activity_id>")
@api
def get_activity(activity_id):
    return activity_service.get_activity(activity_id)
