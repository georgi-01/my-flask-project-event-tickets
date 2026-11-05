VENUE_TYPES = {
    "disco": "дискотека",
    "club": "клуб",
    "bar": "бар",
    "mehana": "механа",
    "krachma": "кръчма",
    "concert": "концерт",
}

DISCOUNT_TYPES = {"disco", "club"}

TICKET_TYPES = {
    "adult": "Възрастен",
    "student": "Студент",
    "child": "Дете",
}

TICKET_STATUSES = {
    "sold": "продаден",
    "reserved": "резервиран",
    "cancelled": "анулиран",
}

ACTIONS = {
    "created": "създаване",
    "updated": "промяна",
    "deleted": "изтриване",
}

ENTITIES = {
    "venue": "място",
    "event": "събитие",
    "ticket": "билет",
    "cash_desk": "каса",
}

SEAT_ROWS = list("ABCDEF")
SEAT_NUMBERS = list(range(1, 11))


def all_seats() -> list[str]:
    return [f"{row}-{number}" for row in SEAT_ROWS for number in SEAT_NUMBERS]


def seat_ok(code: str) -> bool:
    return code in set(all_seats())
