from datetime import datetime

from sqlalchemy.exc import IntegrityError

from app.db import unit_of_work
from app.errors import ConflictError, NotFoundError, ValidationError
from app.events import build_message, publish
from app.formatting import event_dict
from app.labels import VENUE_TYPES
from app.parsing import clean_text, parse_bool, parse_datetime, parse_decimal, parse_int, require_text
from app.repositories import events as event_repo
from app.repositories import venues as venue_repo


def list_events(filters: dict | None = None) -> list[dict]:
    normalized = _filters(filters or {})
    with unit_of_work() as session:
        return [event_dict(row) for row in event_repo.query(session, normalized)]


def list_for_venue(venue_id: int) -> list[dict]:
    with unit_of_work() as session:
        if venue_repo.get(session, venue_id) is None:
            raise NotFoundError("Мястото не е намерено.")
        return [event_dict(row) for row in event_repo.list_for_venue(session, venue_id)]


def get_event(event_id: int) -> dict:
    with unit_of_work() as session:
        event = event_repo.get(session, event_id)
        if event is None:
            raise NotFoundError("Събитието не е намерено.")
        return event_dict(event)


def create_event(data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            venue = venue_repo.get(session, fields["venue_id"])
            if venue is None:
                raise ValidationError("Изберете място.")
            event = event_repo.add(session, fields)
            event.venue = venue
            result = event_dict(event)
            message = build_message(
                "created",
                "event",
                event.id,
                f"Създадено събитие: {event.performer} — {venue.name}",
            )
    except IntegrityError as exc:
        raise ConflictError("Събитието вече съществува.") from exc
    publish(message)
    return result


def update_event(event_id: int, data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            event = event_repo.get(session, event_id)
            if event is None:
                raise NotFoundError("Събитието не е намерено.")
            venue = venue_repo.get(session, fields["venue_id"])
            if venue is None:
                raise ValidationError("Изберете място.")
            for key, value in fields.items():
                setattr(event, key, value)
            session.flush()
            event.venue = venue
            result = event_dict(event)
            message = build_message(
                "updated",
                "event",
                event.id,
                f"Променено събитие: {event.performer} — {venue.name}",
            )
    except IntegrityError as exc:
        raise ConflictError("Събитието вече съществува.") from exc
    publish(message)
    return result


def delete_event(event_id: int) -> None:
    with unit_of_work() as session:
        event = event_repo.get(session, event_id)
        if event is None:
            raise NotFoundError("Събитието не е намерено.")
        message = build_message(
            "deleted",
            "event",
            event.id,
            f"Изтрито събитие: {event.performer} — {event.venue.name}",
        )
        session.delete(event)
    publish(message)


def _fields(data: dict) -> dict:
    venue_id = parse_int(data.get("venue_id"), "Изберете място.")
    performer = require_text(data.get("performer"), 120, "Попълнете изпълнител.")
    if len(performer) < 2:
        raise ValidationError("Името на изпълнителя е твърде кратко.")
    starts_at = parse_datetime(data.get("starts_at"))
    price = parse_decimal(data.get("adult_price"), "Въведете цена.")
    if price <= 0 or price > 10000:
        raise ValidationError("Цената трябва да е между 0,01 и 10000.")
    description = clean_text(data.get("description"), 500)
    return {
        "venue_id": venue_id,
        "performer": performer,
        "starts_at": starts_at,
        "adult_price": price,
        "description": description,
    }


def _filters(filters: dict) -> dict:
    venue_type = str(filters.get("venue_type") or "").strip()
    if venue_type and venue_type not in VENUE_TYPES:
        raise ValidationError("Непознат вид място.")
    raw_date = str(filters.get("date") or "").strip()
    parsed = None
    if raw_date:
        try:
            parsed = datetime.strptime(raw_date, "%Y-%m-%d").date()
        except ValueError as exc:
            raise ValidationError("Невалидна дата.") from exc
    return {
        "q": str(filters.get("q") or "").strip(),
        "city": str(filters.get("city") or "").strip(),
        "venue_type": venue_type,
        "country": str(filters.get("country") or "").strip(),
        "date": parsed,
        "student": parse_bool(filters.get("student")),
        "bottle": parse_bool(filters.get("bottle")),
    }
