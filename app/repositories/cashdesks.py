from sqlalchemy import select
from sqlalchemy.orm import joinedload

from app.models import CashDesk


def add(session, data: dict) -> CashDesk:
    desk = CashDesk(**data)
    session.add(desk)
    session.flush()
    return desk


def get(session, desk_id: int) -> CashDesk | None:
    stmt = select(CashDesk).options(joinedload(CashDesk.venue)).where(CashDesk.id == desk_id)
    return session.scalars(stmt).first()


def list_all(session) -> list[CashDesk]:
    stmt = select(CashDesk).options(joinedload(CashDesk.venue)).order_by(CashDesk.city, CashDesk.name)
    return list(session.scalars(stmt).unique())


def detach_venue(session, venue_id: int) -> None:
    stmt = select(CashDesk).where(CashDesk.venue_id == venue_id)
    for desk in session.scalars(stmt):
        desk.venue_id = None
