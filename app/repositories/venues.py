from sqlalchemy import func, select

from app.models import Venue


def add(session, data: dict) -> Venue:
    venue = Venue(**data)
    session.add(venue)
    session.flush()
    return venue


def get(session, venue_id: int) -> Venue | None:
    return session.get(Venue, venue_id)


def find(session, name: str, city: str) -> Venue | None:
    stmt = select(Venue).where(Venue.name == name, Venue.city == city)
    return session.scalars(stmt).first()


def list_all(session) -> list[Venue]:
    stmt = select(Venue).order_by(Venue.city, Venue.name, Venue.id)
    return list(session.scalars(stmt))


def cities(session) -> list[str]:
    stmt = select(Venue.city).distinct().order_by(Venue.city)
    return list(session.scalars(stmt))


def countries(session) -> list[str]:
    stmt = select(Venue.country).distinct().order_by(Venue.country)
    return list(session.scalars(stmt))


def count(session) -> int:
    return session.scalar(select(func.count()).select_from(Venue)) or 0
