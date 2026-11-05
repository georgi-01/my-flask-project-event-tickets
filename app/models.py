from datetime import datetime, timezone
from decimal import Decimal

from sqlalchemy import Boolean, DateTime, ForeignKey, Numeric, String, Text, UniqueConstraint
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column, relationship


def utcnow() -> datetime:
    return datetime.now(timezone.utc).replace(microsecond=0, tzinfo=None)


class Base(DeclarativeBase):
    pass


class Venue(Base):
    __tablename__ = "venues"
    __table_args__ = (UniqueConstraint("name", "city", name="uq_venue_name_city"),)

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120))
    venue_type: Mapped[str] = mapped_column(String(20))
    city: Mapped[str] = mapped_column(String(80))
    address: Mapped[str] = mapped_column(String(200))
    country: Mapped[str] = mapped_column(String(40))
    free_student_entry: Mapped[bool] = mapped_column(Boolean, default=False)
    bottle_discount: Mapped[bool] = mapped_column(Boolean, default=False)
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    events: Mapped[list["Event"]] = relationship(
        back_populates="venue", cascade="all, delete-orphan"
    )


class Event(Base):
    __tablename__ = "events"
    __table_args__ = (
        UniqueConstraint("venue_id", "performer", "starts_at", name="uq_event_slot"),
    )

    id: Mapped[int] = mapped_column(primary_key=True)
    venue_id: Mapped[int] = mapped_column(ForeignKey("venues.id", ondelete="CASCADE"), index=True)
    performer: Mapped[str] = mapped_column(String(120))
    starts_at: Mapped[datetime] = mapped_column(DateTime, index=True)
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    description: Mapped[str] = mapped_column(Text, default="")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    venue: Mapped[Venue] = relationship(back_populates="events")
    tickets: Mapped[list["Ticket"]] = relationship(
        back_populates="event", cascade="all, delete-orphan"
    )


class CashDesk(Base):
    __tablename__ = "cash_desks"

    id: Mapped[int] = mapped_column(primary_key=True)
    name: Mapped[str] = mapped_column(String(120), unique=True)
    city: Mapped[str] = mapped_column(String(80))
    address: Mapped[str] = mapped_column(String(200), default="")
    operator_name: Mapped[str] = mapped_column(String(120))
    venue_id: Mapped[int | None] = mapped_column(
        ForeignKey("venues.id", ondelete="SET NULL"), nullable=True, index=True
    )
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    venue: Mapped[Venue | None] = relationship()
    tickets: Mapped[list["Ticket"]] = relationship(back_populates="cash_desk")


class Ticket(Base):
    __tablename__ = "tickets"

    id: Mapped[int] = mapped_column(primary_key=True)
    event_id: Mapped[int] = mapped_column(ForeignKey("events.id", ondelete="CASCADE"), index=True)
    cash_desk_id: Mapped[int | None] = mapped_column(
        ForeignKey("cash_desks.id"), nullable=True, index=True
    )
    ticket_type: Mapped[str] = mapped_column(String(20))
    seat_code: Mapped[str] = mapped_column(String(8))
    price: Mapped[Decimal] = mapped_column(Numeric(10, 2))
    buyer_name: Mapped[str] = mapped_column(String(120))
    status: Mapped[str] = mapped_column(String(20), default="sold")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow)

    event: Mapped[Event] = relationship(back_populates="tickets")
    cash_desk: Mapped[CashDesk | None] = relationship(back_populates="tickets")


class Activity(Base):
    __tablename__ = "activity"

    id: Mapped[int] = mapped_column(primary_key=True)
    message_id: Mapped[str] = mapped_column(String(64), unique=True)
    action: Mapped[str] = mapped_column(String(20))
    entity: Mapped[str] = mapped_column(String(20))
    entity_id: Mapped[int] = mapped_column(index=True)
    summary: Mapped[str] = mapped_column(String(300))
    created_at: Mapped[datetime] = mapped_column(DateTime, default=utcnow, index=True)
