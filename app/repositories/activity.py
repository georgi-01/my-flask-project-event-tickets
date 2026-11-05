from sqlalchemy import func, select

from app.models import Activity


def add(session, payload: dict) -> Activity:
    row = Activity(
        message_id=str(payload["message_id"])[:64],
        action=str(payload["action"])[:20],
        entity=str(payload["entity"])[:20],
        entity_id=int(payload["entity_id"]),
        summary=str(payload["summary"])[:300],
    )
    session.add(row)
    session.flush()
    return row


def get(session, activity_id: int) -> Activity | None:
    return session.get(Activity, activity_id)


def get_by_message_id(session, message_id: str) -> Activity | None:
    stmt = select(Activity).where(Activity.message_id == message_id)
    return session.scalars(stmt).first()


def list_all(session) -> list[Activity]:
    stmt = select(Activity).order_by(Activity.created_at.desc(), Activity.id.desc())
    return list(session.scalars(stmt))


def count(session) -> int:
    return session.scalar(select(func.count()).select_from(Activity)) or 0
