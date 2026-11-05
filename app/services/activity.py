from sqlalchemy.exc import IntegrityError

from app.db import unit_of_work
from app.errors import NotFoundError, ValidationError
from app.formatting import activity_dict
from app.repositories import activity as activity_repo


def list_activity() -> list[dict]:
    with unit_of_work() as session:
        return [activity_dict(row) for row in activity_repo.list_all(session)]


def get_activity(activity_id: int) -> dict:
    with unit_of_work() as session:
        row = activity_repo.get(session, activity_id)
        if row is None:
            raise NotFoundError("Записът не е намерен.")
        return activity_dict(row)


def count_activity() -> int:
    with unit_of_work() as session:
        return activity_repo.count(session)


def record_activity(payload: dict) -> dict | None:
    required = ("message_id", "action", "entity", "entity_id", "summary")
    if any(payload.get(key) in (None, "") for key in required):
        raise ValidationError("Непълен запис за дневника.")
    try:
        with unit_of_work() as session:
            if activity_repo.get_by_message_id(session, str(payload["message_id"])):
                return None
            row = activity_repo.add(session, payload)
            return activity_dict(row)
    except IntegrityError:
        return None
