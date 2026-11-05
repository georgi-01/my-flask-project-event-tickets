from sqlalchemy.exc import IntegrityError

from app.db import unit_of_work
from app.errors import ConflictError, NotFoundError, ValidationError
from app.events import build_message, publish
from app.formatting import venue_dict
from app.labels import DISCOUNT_TYPES, VENUE_TYPES
from app.parsing import clean_text, parse_bool, require_text
from app.repositories import cashdesks as cashdesk_repo
from app.repositories import venues as venue_repo


def list_venues() -> list[dict]:
    with unit_of_work() as session:
        return [venue_dict(row) for row in venue_repo.list_all(session)]


def list_cities() -> list[str]:
    with unit_of_work() as session:
        return venue_repo.cities(session)


def list_countries() -> list[str]:
    with unit_of_work() as session:
        return venue_repo.countries(session)


def get_venue(venue_id: int) -> dict:
    with unit_of_work() as session:
        venue = venue_repo.get(session, venue_id)
        if venue is None:
            raise NotFoundError("Мястото не е намерено.")
        return venue_dict(venue)


def create_venue(data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            venue = venue_repo.add(session, fields)
            result = venue_dict(venue)
            message = build_message(
                "created",
                "venue",
                venue.id,
                f"Създадено място „{venue.name}“ ({result['venue_type_label']}, {venue.city})",
            )
    except IntegrityError as exc:
        raise ConflictError("Това място вече е въведено.") from exc
    publish(message)
    return result


def update_venue(venue_id: int, data: dict) -> dict:
    fields = _fields(data)
    try:
        with unit_of_work() as session:
            venue = venue_repo.get(session, venue_id)
            if venue is None:
                raise NotFoundError("Мястото не е намерено.")
            for key, value in fields.items():
                setattr(venue, key, value)
            session.flush()
            result = venue_dict(venue)
            message = build_message(
                "updated",
                "venue",
                venue.id,
                f"Променено място „{venue.name}“ ({result['venue_type_label']}, {venue.city})",
            )
    except IntegrityError as exc:
        raise ConflictError("Това място вече е въведено.") from exc
    publish(message)
    return result


def delete_venue(venue_id: int) -> None:
    with unit_of_work() as session:
        venue = venue_repo.get(session, venue_id)
        if venue is None:
            raise NotFoundError("Мястото не е намерено.")
        message = build_message(
            "deleted",
            "venue",
            venue.id,
            f"Изтрито място „{venue.name}“ ({venue.city})",
        )
        cashdesk_repo.detach_venue(session, venue.id)
        session.delete(venue)
    publish(message)


def _fields(data: dict) -> dict:
    name = require_text(data.get("name"), 120, "Попълнете име.")
    if len(name) < 2:
        raise ValidationError("Името е твърде кратко.")
    venue_type = clean_text(data.get("venue_type"), 20)
    if venue_type not in VENUE_TYPES:
        raise ValidationError("Изберете вид място.")
    city = require_text(data.get("city"), 80, "Попълнете град.")
    address = require_text(data.get("address"), 200, "Попълнете адрес.")
    country = require_text(data.get("country"), 40, "Попълнете държава.")
    description = clean_text(data.get("description"), 500)
    free_student = parse_bool(data.get("free_student_entry"))
    bottle = parse_bool(data.get("bottle_discount"))
    if venue_type not in DISCOUNT_TYPES and (free_student or bottle):
        raise ValidationError("Отстъпките са само за дискотека и клуб.")
    return {
        "name": name,
        "venue_type": venue_type,
        "city": city,
        "address": address,
        "country": country,
        "description": description,
        "free_student_entry": free_student,
        "bottle_discount": bottle,
    }
