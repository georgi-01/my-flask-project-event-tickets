from datetime import datetime
from decimal import Decimal, ROUND_HALF_UP

from app.labels import ACTIONS, ENTITIES, TICKET_STATUSES, TICKET_TYPES, VENUE_TYPES

TWOPLACES = Decimal("0.01")
MONTHS = [
    "януари",
    "февруари",
    "март",
    "април",
    "май",
    "юни",
    "юли",
    "август",
    "септември",
    "октомври",
    "ноември",
    "декември",
]
MONTHS_SHORT = [
    "яну",
    "фев",
    "мар",
    "апр",
    "май",
    "юни",
    "юли",
    "авг",
    "сеп",
    "окт",
    "ное",
    "дек",
]


def money(value) -> Decimal:
    return Decimal(str(value)).quantize(TWOPLACES, rounding=ROUND_HALF_UP)


def money_str(value) -> str:
    return f"{money(value)}"


def format_price(value) -> str:
    number = money(value)
    sign = "−" if number < 0 else ""
    whole, frac = f"{abs(number):.2f}".split(".")
    grouped = f"{int(whole):,}".replace(",", " ")
    return f"{sign}{grouped},{frac} €"


def format_datetime(value: datetime) -> str:
    return f"{value.day} {MONTHS[value.month - 1]} {value.year}, {value:%H:%M}"


def count_label(count: int, one: str, many: str) -> str:
    word = one if count == 1 else many
    return f"{count} {word}"


def venue_dict(venue) -> dict:
    return {
        "id": venue.id,
        "name": venue.name,
        "venue_type": venue.venue_type,
        "venue_type_label": VENUE_TYPES.get(venue.venue_type, venue.venue_type),
        "city": venue.city,
        "address": venue.address,
        "country": venue.country,
        "free_student_entry": bool(venue.free_student_entry),
        "bottle_discount": bool(venue.bottle_discount),
        "description": venue.description or "",
    }


def event_dict(event) -> dict:
    venue = event.venue
    adult = money(event.price)
    student = Decimal("0.00") if venue.free_student_entry else None
    child = None if venue.venue_type == "disco" else money(adult / Decimal(2))
    return {
        "id": event.id,
        "venue_id": venue.id,
        "venue_name": venue.name,
        "venue_type": venue.venue_type,
        "venue_type_label": VENUE_TYPES.get(venue.venue_type, venue.venue_type),
        "city": venue.city,
        "country": venue.country,
        "address": venue.address,
        "performer": event.performer,
        "starts_at": event.starts_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "starts_input": event.starts_at.strftime("%Y-%m-%dT%H:%M"),
        "starts_label": format_datetime(event.starts_at),
        "day": f"{event.starts_at.day:02d}",
        "month_short": MONTHS_SHORT[event.starts_at.month - 1],
        "time_label": event.starts_at.strftime("%H:%M"),
        "price": money_str(adult),
        "price_label": format_price(adult),
        "student_price": None if student is None else money_str(student),
        "student_price_label": None if student is None else format_price(student),
        "child_price": None if child is None else money_str(child),
        "child_price_label": None if child is None else format_price(child),
        "free_student_entry": bool(venue.free_student_entry),
        "bottle_discount": bool(venue.bottle_discount),
        "description": event.description or "",
    }


def ticket_dict(ticket) -> dict:
    event = ticket.event
    venue = event.venue
    desk = ticket.cash_desk
    return {
        "id": ticket.id,
        "event_id": event.id,
        "performer": event.performer,
        "venue_name": venue.name,
        "city": venue.city,
        "starts_label": format_datetime(event.starts_at),
        "cash_desk_id": None if desk is None else desk.id,
        "cash_desk_name": None if desk is None else desk.name,
        "ticket_type": ticket.ticket_type,
        "ticket_type_label": TICKET_TYPES.get(ticket.ticket_type, ticket.ticket_type),
        "seat_code": ticket.seat_code,
        "price": money_str(ticket.price),
        "price_label": format_price(ticket.price),
        "buyer_name": ticket.buyer_name,
        "status": ticket.status,
        "status_label": TICKET_STATUSES.get(ticket.status, ticket.status),
    }


def desk_dict(desk) -> dict:
    venue = desk.venue
    return {
        "id": desk.id,
        "name": desk.name,
        "city": desk.city,
        "address": desk.address or "",
        "operator_name": desk.operator_name,
        "venue_id": desk.venue_id,
        "venue_name": None if venue is None else venue.name,
    }


def activity_dict(row) -> dict:
    return {
        "id": row.id,
        "message_id": row.message_id,
        "action": row.action,
        "action_label": ACTIONS.get(row.action, row.action),
        "entity": row.entity,
        "entity_label": ENTITIES.get(row.entity, row.entity),
        "entity_id": row.entity_id,
        "summary": row.summary,
        "created_at": row.created_at.strftime("%Y-%m-%dT%H:%M:%S"),
        "created_label": format_datetime(row.created_at),
    }
