from datetime import datetime, timedelta

from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import Event, Venue


def add(session, data: dict) -> Event:
    event = Event(**data)
    session.add(event)
    session.flush()
    return event


def get(session, event_id: int) -> Event | None:
    stmt = select(Event).options(joinedload(Event.venue)).where(Event.id == event_id)
    return session.scalars(stmt).first()


def list_for_venue(session, venue_id: int) -> list[Event]:
    stmt = (
        select(Event)
        .options(joinedload(Event.venue))
        .where(Event.venue_id == venue_id)
        .order_by(Event.starts_at, Event.id)
    )
    return list(session.scalars(stmt).unique())


def query(session, filters: dict) -> list[Event]:
    stmt = (
        select(Event)
        .join(Venue)
        .options(joinedload(Event.venue))
        .order_by(Event.starts_at, Event.id)
    )
    if filters.get("city"):
        stmt = stmt.where(Venue.city == filters["city"])
    if filters.get("venue_type"):
        stmt = stmt.where(Venue.venue_type == filters["venue_type"])
    if filters.get("country"):
        stmt = stmt.where(Venue.country == filters["country"])
    if filters.get("student"):
        stmt = stmt.where(Venue.free_student_entry.is_(True))
    if filters.get("bottle"):
        stmt = stmt.where(Venue.bottle_discount.is_(True))
    if filters.get("date"):
        start = datetime.combine(filters["date"], datetime.min.time())
        stmt = stmt.where(Event.starts_at >= start, Event.starts_at < start + timedelta(days=1))
    rows = list(session.scalars(stmt).unique())
    needle = (filters.get("q") or "").casefold()
    if not needle:
        return rows
    return [
        row
        for row in rows
        if needle in row.performer.casefold()
        or needle in row.venue.name.casefold()
        or needle in row.venue.city.casefold()
    ]
