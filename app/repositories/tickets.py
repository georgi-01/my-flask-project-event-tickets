from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Event, Ticket


def add(session, data: dict) -> Ticket:
    ticket = Ticket(**data)
    session.add(ticket)
    session.flush()
    return ticket


def get(session, ticket_id: int) -> Ticket | None:
    stmt = (
        select(Ticket)
        .options(
            joinedload(Ticket.event).joinedload(Event.venue),
            joinedload(Ticket.cash_desk),
        )
        .where(Ticket.id == ticket_id)
    )
    return session.scalars(stmt).first()


def list_all(session) -> list[Ticket]:
    stmt = (
        select(Ticket)
        .options(
            joinedload(Ticket.event).joinedload(Event.venue),
            joinedload(Ticket.cash_desk),
        )
        .order_by(Ticket.id.desc())
    )
    return list(session.scalars(stmt).unique())


def occupied(session, event_id: int, exclude_id: int | None = None) -> set[str]:
    stmt = select(Ticket.seat_code).where(
        Ticket.event_id == event_id,
        Ticket.status != "cancelled",
    )
    if exclude_id is not None:
        stmt = stmt.where(Ticket.id != exclude_id)
    return set(session.scalars(stmt))


def count_for_desk(session, desk_id: int) -> int:
    stmt = select(Ticket.id).where(Ticket.cash_desk_id == desk_id)
    return len(list(session.scalars(stmt)))
