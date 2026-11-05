from datetime import datetime
from decimal import Decimal, InvalidOperation

from app.errors import ValidationError


def clean_text(value, limit: int) -> str:
    if value is None:
        return ""
    text = str(value).strip()
    if len(text) > limit:
        return text[:limit]
    return text


def require_text(value, limit: int, message: str) -> str:
    text = clean_text(value, limit)
    if not text:
        raise ValidationError(message)
    return text


def parse_bool(value) -> bool:
    if isinstance(value, bool):
        return value
    if value is None:
        return False
    return str(value).strip().lower() in {"1", "true", "yes", "on", "да"}


def parse_decimal(value, message: str = "Въведете цена.") -> Decimal:
    if isinstance(value, bool) or value is None:
        raise ValidationError(message)
    if isinstance(value, Decimal):
        number = value
    elif isinstance(value, (int, float)):
        number = Decimal(str(value))
    else:
        raw = (
            str(value)
            .strip()
            .replace("лв.", "")
            .replace("лв", "")
            .replace(" ", "")
            .replace(",", ".")
        )
        if not raw:
            raise ValidationError(message)
        try:
            number = Decimal(raw)
        except InvalidOperation as exc:
            raise ValidationError(message) from exc
    return number.quantize(Decimal("0.01"))


def parse_datetime(value, message: str = "Въведете дата и час.") -> datetime:
    if isinstance(value, datetime):
        return value.replace(tzinfo=None, microsecond=0)
    if value is None:
        raise ValidationError(message)
    raw = str(value).strip()
    for fmt in (
        "%Y-%m-%dT%H:%M",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M",
        "%Y-%m-%d %H:%M:%S",
    ):
        try:
            return datetime.strptime(raw, fmt)
        except ValueError:
            continue
    raise ValidationError(message)


def parse_int(value, message: str) -> int:
    if isinstance(value, bool) or value is None or str(value).strip() == "":
        raise ValidationError(message)
    try:
        return int(value)
    except (TypeError, ValueError) as exc:
        raise ValidationError(message) from exc


def parse_optional_int(value) -> int | None:
    if value is None or str(value).strip() == "":
        return None
    return parse_int(value, "Невалиден номер.")


def parse_seats(value) -> list[str]:
    if value is None:
        return []
    if isinstance(value, list):
        parts = [str(item) for item in value]
    else:
        raw = str(value).replace(";", ",").replace("\n", ",")
        parts = raw.replace(" ", ",").split(",")
    seats: list[str] = []
    seen: set[str] = set()
    for part in parts:
        code = part.strip().upper()
        if not code or code in seen:
            continue
        seen.add(code)
        seats.append(code)
    return seats
