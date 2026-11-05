from decimal import Decimal

from app.db import unit_of_work
from app.errors import ConflictError, NotFoundError, ValidationError
from app.events import build_message, publish
from app.formatting import money, ticket_dict
from app.labels import SEAT_ROWS, TICKET_STATUSES, TICKET_TYPES, all_seats, seat_ok
from app.parsing import clean_text, parse_int, parse_seats, require_text
from app.repositories import cashdesks as cashdesk_repo
from app.repositories import events as event_repo
from app.repositories import tickets as ticket_repo


def list_tickets() -> list[dict]:
    with unit_of_work() as session:
        return [ticket_dict(row) for row in ticket_repo.list_all(session)]


def get_ticket(ticket_id: int) -> dict:
    with unit_of_work() as session:
        ticket = ticket_repo.get(session, ticket_id)
        if ticket is None:
            raise NotFoundError("Билетът не е намерен.")
        return ticket_dict(ticket)


def seat_map(event_id: int) -> list[dict]:
    with unit_of_work() as session:
        if event_repo.get(session, event_id) is None:
            raise NotFoundError("Събитието не е намерено.")
        taken = ticket_repo.occupied(session, event_id)
    grouped = []
    for row in SEAT_ROWS:
        seats = []
        for code in all_seats():
            if not code.startswith(f"{row}-"):
                continue
            number = int(code.split("-", 1)[1])
            seats.append({"code": code, "number": number, "taken": code in taken})
        grouped.append({"row": row, "seats": seats})
    return grouped


def create_ticket(data: dict) -> dict:
    messages = []
    with unit_of_work() as session:
        result = _insert(session, data, messages)
    for message in messages:
        publish(message)
    return result


def purchase(event_id: int, data: dict) -> list[dict]:
    seats = parse_seats(data.get("seats", data.get("seat_code")))
    if not seats:
        raise ValidationError("Изберете поне едно място.")
    if len(seats) > 10:
        raise ValidationError("Най-много 10 билета наведнъж.")
    for seat in seats:
        if not seat_ok(seat):
            raise ValidationError(f"Непознато място: {seat}.")
    payload = {
        "event_id": event_id,
        "cash_desk_id": data.get("cash_desk_id"),
        "ticket_type": data.get("ticket_type"),
        "buyer_name": data.get("buyer_name"),
        "status": "sold",
    }
    created = []
    messages = []
    with unit_of_work() as session:
        event, desk, ticket_type, buyer, price = _context(session, payload)
        occupied = ticket_repo.occupied(session, event.id)
        busy = [seat for seat in seats if seat in occupied]
        if busy:
            raise ConflictError(f"Заети места: {', '.join(busy)}.")
        for seat in seats:
            created.append(
                _save(
                    session,
                    event,
                    desk,
                    ticket_type,
                    seat,
                    buyer,
                    price,
                    "sold",
                    messages,
                    verb="Продаден",
                )
            )
    for message in messages:
        publish(message)
    return created


def update_ticket(ticket_id: int, data: dict) -> dict:
    messages = []
    with unit_of_work() as session:
        current = ticket_repo.get(session, ticket_id)
        if current is None:
            raise NotFoundError("Билетът не е намерен.")
        event, desk, ticket_type, buyer, price = _context(session, data)
        seat = _seat(data.get("seat_code"))
        status = _status(data.get("status"))
        if status != "cancelled" and seat in ticket_repo.occupied(session, event.id, exclude_id=current.id):
            raise ConflictError(f"Мястото {seat} е заето.")
        current.event_id = event.id
        current.cash_desk_id = desk.id
        current.ticket_type = ticket_type
        current.seat_code = seat
        current.buyer_name = buyer
        current.price = price
        current.status = status
        current.event = event
        current.cash_desk = desk
        session.flush()
        result = ticket_dict(current)
        messages.append(
            build_message(
                "updated",
                "ticket",
                current.id,
                f"Променен билет {seat} — {event.performer}, {event.venue.name}",
            )
        )
    for message in messages:
        publish(message)
    return result


def delete_ticket(ticket_id: int) -> None:
    with unit_of_work() as session:
        ticket = ticket_repo.get(session, ticket_id)
        if ticket is None:
            raise NotFoundError("Билетът не е намерен.")
        message = build_message(
            "deleted",
            "ticket",
            ticket.id,
            f"Изтрит билет {ticket.seat_code} — {ticket.event.performer}, {ticket.event.venue.name}",
        )
        session.delete(ticket)
    publish(message)


def price_for(event, ticket_type: str) -> Decimal:
    adult = money(event.adult_price)
    if ticket_type == "adult":
        return adult
    if ticket_type == "student":
        if not event.venue.free_student_entry:
            raise ValidationError("Това място няма безплатен студентски вход.")
        return Decimal("0.00")
    if ticket_type == "child":
        if event.venue.venue_type == "disco":
            raise ValidationError("За дискотека няма детски билет.")
        return money(adult / Decimal(2))
    raise ValidationError("Изберете вид билет.")


def _insert(session, data: dict, messages: list) -> dict:
    event, desk, ticket_type, buyer, price = _context(session, data)
    seat = _seat(data.get("seat_code"))
    status = _status(data.get("status") or "sold")
    if status != "cancelled" and seat in ticket_repo.occupied(session, event.id):
        raise ConflictError(f"Мястото {seat} е заето.")
    verb = {"sold": "Продаден", "reserved": "Резервиран", "cancelled": "Анулиран"}[status]
    return _save(session, event, desk, ticket_type, seat, buyer, price, status, messages, verb=verb)


def _save(session, event, desk, ticket_type, seat, buyer, price, status, messages, verb: str) -> dict:
    ticket = ticket_repo.add(
        session,
        {
            "event_id": event.id,
            "cash_desk_id": desk.id,
            "ticket_type": ticket_type,
            "seat_code": seat,
            "buyer_name": buyer,
            "price": price,
            "status": status,
        },
    )
    ticket.event = event
    ticket.cash_desk = desk
    label = TICKET_TYPES[ticket_type]
    messages.append(
        build_message(
            "created",
            "ticket",
            ticket.id,
            f"{verb} билет {seat} ({label}) — {event.performer}, {event.venue.name}",
        )
    )
    return ticket_dict(ticket)


def _context(session, data: dict):
    event_id = parse_int(data.get("event_id"), "Изберете събитие.")
    event = event_repo.get(session, event_id)
    if event is None:
        raise ValidationError("Изберете събитие.")
    desk_id = parse_int(data.get("cash_desk_id"), "Изберете каса.")
    desk = cashdesk_repo.get(session, desk_id)
    if desk is None:
        raise ValidationError("Изберете каса.")
    ticket_type = clean_text(data.get("ticket_type"), 20)
    if ticket_type not in TICKET_TYPES:
        raise ValidationError("Изберете вид билет.")
    buyer = require_text(data.get("buyer_name"), 120, "Попълнете име на купувач.")
    if len(buyer) < 2:
        raise ValidationError("Името на купувача е твърде кратко.")
    price = price_for(event, ticket_type)
    return event, desk, ticket_type, buyer, price


def _seat(value) -> str:
    seats = parse_seats(value)
    if len(seats) != 1 or not seat_ok(seats[0]):
        raise ValidationError("Непознато място.")
    return seats[0]


def _status(value) -> str:
    status = clean_text(value, 20)
    if status not in TICKET_STATUSES:
        raise ValidationError("Изберете статус.")
    return status
