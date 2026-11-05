from sqlalchemy.exc import IntegrityError

from app.db import unit_of_work
from app.errors import ConflictError, NotFoundError, ValidationError
from app.events import build_message, publish
from app.formatting import desk_dict
from app.parsing import parse_optional_int, require_text
from app.repositories import cashdesks as cashdesk_repo
from app.repositories import tickets as ticket_repo
from app.repositories import venues as venue_repo


def list_cashdesks() -> list[dict]:
    with unit_of_work() as session:
        return [desk_dict(row) for row in cashdesk_repo.list_all(session)]


def get_cashdesk(desk_id: int) -> dict:
    with unit_of_work() as session:
        desk = cashdesk_repo.get(session, desk_id)
        if desk is None:
            raise NotFoundError("Касата не е намерена.")
        return desk_dict(desk)


def create_cashdesk(data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            _ensure_venue(session, fields.get("venue_id"))
            desk = cashdesk_repo.add(session, fields)
            desk.venue = venue_repo.get(session, desk.venue_id) if desk.venue_id else None
            result = desk_dict(desk)
            message = build_message(
                "created",
                "cash_desk",
                desk.id,
                f"Създадена каса „{desk.name}“ ({desk.city})",
            )
    except IntegrityError as exc:
        raise ConflictError("Каса с това име вече съществува.") from exc
    publish(message)
    return result


def update_cashdesk(desk_id: int, data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            desk = cashdesk_repo.get(session, desk_id)
            if desk is None:
                raise NotFoundError("Касата не е намерена.")
            _ensure_venue(session, fields.get("venue_id"))
            for key, value in fields.items():
                setattr(desk, key, value)
            session.flush()
            desk.venue = venue_repo.get(session, desk.venue_id) if desk.venue_id else None
            result = desk_dict(desk)
            message = build_message(
                "updated",
                "cash_desk",
                desk.id,
                f"Променена каса „{desk.name}“ ({desk.city})",
            )
    except IntegrityError as exc:
        raise ConflictError("Каса с това име вече съществува.") from exc
    publish(message)
    return result


def delete_cashdesk(desk_id: int) -> None:
    with unit_of_work() as session:
        desk = cashdesk_repo.get(session, desk_id)
        if desk is None:
            raise NotFoundError("Касата не е намерена.")
        if ticket_repo.count_for_desk(session, desk.id):
            raise ConflictError("Касата има билети.")
        message = build_message(
            "deleted",
            "cash_desk",
            desk.id,
            f"Изтрита каса „{desk.name}“",
        )
        session.delete(desk)
    publish(message)


def _ensure_venue(session, venue_id: int | None) -> None:
    if venue_id is None:
        return
    if venue_repo.get(session, venue_id) is None:
        raise ValidationError("Изберете място.")


def _fields(data: dict) -> dict:
    name = require_text(data.get("name"), 120, "Попълнете име.")
    if len(name) < 2:
        raise ValidationError("Името е твърде кратко.")
    city = require_text(data.get("city"), 80, "Попълнете град.")
    operator = require_text(data.get("operator_name"), 120, "Попълнете оператор.")
    if len(operator) < 2:
        raise ValidationError("Името на оператора е твърде кратко.")
    address = require_text(data.get("address"), 200, "Попълнете адрес.")
    venue_id = parse_optional_int(data.get("venue_id"))
    return {
        "name": name,
        "city": city,
        "address": address,
        "operator_name": operator,
        "venue_id": venue_id,
    }
