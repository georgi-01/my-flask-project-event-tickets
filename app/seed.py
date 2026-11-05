import os
import time

from dotenv import load_dotenv

from app.db import init_db, unit_of_work
from app.repositories import venues as venue_repo
from app.services import activity as activity_service
from app.services import cashdesks as cashdesk_service
from app.services import events as event_service
from app.services import tickets as ticket_service
from app.services import venues as venue_service

VENUES = [
    {
        "name": "Ялта",
        "venue_type": "disco",
        "city": "София",
        "address": "бул. „България“ 1",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Дискотека до НДК.",
    },
    {
        "name": "Tell Me",
        "venue_type": "club",
        "city": "София",
        "address": "Студентски град, ул. „8-ми декември“ 15",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Клуб в Студентски град.",
    },
    {
        "name": "Купе",
        "venue_type": "disco",
        "city": "София",
        "address": "ул. „Цар Освободител“ 2",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Дискотека без студентски вход и без намаление за бутилка.",
    },
    {
        "name": "Строежа",
        "venue_type": "club",
        "city": "София",
        "address": "ул. „Пиротска“ 5",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Клуб без отстъпки.",
    },
    {
        "name": "Спутник",
        "venue_type": "bar",
        "city": "София",
        "address": "ул. „Шишман“ 22",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Бар в центъра.",
    },
    {
        "name": "Механа Под липите",
        "venue_type": "mehana",
        "city": "София",
        "address": "ул. „Сан Стефано“ 14",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Механа с вечерна програма.",
    },
    {
        "name": "Кръчма При бай Миле",
        "venue_type": "krachma",
        "city": "София",
        "address": "ул. „Граф Игнатиев“ 18",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Кръчма с малка сцена.",
    },
    {
        "name": "Зала България",
        "venue_type": "concert",
        "city": "София",
        "address": "ул. „Аксаков“ 1",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Концертна зала.",
    },
    {
        "name": "Петъното",
        "venue_type": "disco",
        "city": "Пловдив",
        "address": "ул. „Капитан Райчо“ 4",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Дискотека в Капана.",
    },
    {
        "name": "Клуб Капана",
        "venue_type": "club",
        "city": "Пловдив",
        "address": "ул. „Братска“ 3",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Клуб в Капана.",
    },
    {
        "name": "Механа Пълдин",
        "venue_type": "mehana",
        "city": "Пловдив",
        "address": "ул. „Княз Александър I“ 15",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Механа в центъра на Пловдив.",
    },
    {
        "name": "Бар Капана",
        "venue_type": "bar",
        "city": "Пловдив",
        "address": "ул. „Братска“ 7",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Бар с вечерна сцена.",
    },
    {
        "name": "Cubo",
        "venue_type": "club",
        "city": "Варна",
        "address": "бул. „Сливница“ 2",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Клуб във Варна без отстъпки.",
    },
    {
        "name": "Планет",
        "venue_type": "disco",
        "city": "Варна",
        "address": "бул. „Княз Борис I“ 65",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Дискотека до Морската градина.",
    },
    {
        "name": "Кръчма При Рибаря",
        "venue_type": "krachma",
        "city": "Варна",
        "address": "ул. „Преслав“ 9",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Кръчма близо до морето.",
    },
    {
        "name": "Летен театър",
        "venue_type": "concert",
        "city": "Варна",
        "address": "Морска градина",
        "country": "България",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Лятна сцена във Варна.",
    },
    {
        "name": "Драгстор",
        "venue_type": "disco",
        "city": "Белград",
        "address": "Цетињска 15",
        "country": "Сърбия",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Дискотека в Белград.",
    },
    {
        "name": "Кафана Знак питања",
        "venue_type": "krachma",
        "city": "Белград",
        "address": "Краља Петра 6",
        "country": "Сърбия",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Кафана със сцена.",
    },
    {
        "name": "Штарк арена",
        "venue_type": "concert",
        "city": "Белград",
        "address": "Булевар Арсенија Чарнојевића 58",
        "country": "Сърбия",
        "free_student_entry": False,
        "bottle_discount": False,
        "description": "Концертна арена.",
    },
]

EVENTS = [
    {"venue": "Ялта", "city": "София", "performer": "Киара", "starts_at": "2026-11-07T23:00", "price": "15.00", "description": "Нощ с Киара."},
    {"venue": "Tell Me", "city": "София", "performer": "Галин", "starts_at": "2026-11-08T22:30", "price": "18.00", "description": "Клубна вечер с Галин."},
    {"venue": "Купе", "city": "София", "performer": "Селина", "starts_at": "2026-11-13T23:30", "price": "20.00", "description": "Селина в Купе."},
    {"venue": "Строежа", "city": "София", "performer": "Мирела", "starts_at": "2026-11-14T23:00", "price": "18.00", "description": "Мирела на Строежа."},
    {"venue": "Спутник", "city": "София", "performer": "Азис", "starts_at": "2026-11-15T21:00", "price": "13.00", "description": "Азис в бара."},
    {"venue": "Механа Под липите", "city": "София", "performer": "Силвър", "starts_at": "2026-11-20T19:30", "price": "10.00", "description": "Вечер със Силвър."},
    {"venue": "Кръчма При бай Миле", "city": "София", "performer": "Диона", "starts_at": "2026-11-21T20:00", "price": "8.00", "description": "Диона на малка сцена."},
    {"venue": "Зала България", "city": "София", "performer": "Ксиор", "starts_at": "2026-11-28T19:00", "price": "28.00", "description": "Концерт на Ксиор."},
    {"venue": "Петъното", "city": "Пловдив", "performer": "Сис и Джордан", "starts_at": "2026-11-14T23:00", "price": "13.00", "description": "Сис и Джордан в Петъното."},
    {"venue": "Клуб Капана", "city": "Пловдив", "performer": "Киара", "starts_at": "2026-11-21T22:00", "price": "15.00", "description": "Киара в Капана."},
    {"venue": "Механа Пълдин", "city": "Пловдив", "performer": "Галин", "starts_at": "2026-12-04T19:00", "price": "11.00", "description": "Галин в механата."},
    {"venue": "Бар Капана", "city": "Пловдив", "performer": "Селина", "starts_at": "2026-12-05T21:00", "price": "9.00", "description": "Селина в бара."},
    {"venue": "Cubo", "city": "Варна", "performer": "Мирела", "starts_at": "2026-12-11T23:30", "price": "15.00", "description": "Мирела в Cubo."},
    {"venue": "Планет", "city": "Варна", "performer": "Азис", "starts_at": "2026-12-12T23:00", "price": "14.00", "description": "Азис в Планет."},
    {"venue": "Кръчма При Рибаря", "city": "Варна", "performer": "Силвър", "starts_at": "2026-12-18T20:30", "price": "6.00", "description": "Силвър край морето."},
    {"venue": "Летен театър", "city": "Варна", "performer": "Диона", "starts_at": "2026-12-19T19:00", "price": "23.00", "description": "Диона на летния театър."},
    {"venue": "Драгстор", "city": "Белград", "performer": "Цеца", "starts_at": "2026-11-22T23:00", "price": "20.00", "description": "Цеца в Драгстор."},
    {"venue": "Драгстор", "city": "Белград", "performer": "Сека Алексич", "starts_at": "2026-12-06T23:00", "price": "20.00", "description": "Сека Алексич в Драгстор."},
    {"venue": "Кафана Знак питања", "city": "Белград", "performer": "Аца Лукас", "starts_at": "2026-12-13T21:00", "price": "15.00", "description": "Аца Лукас в кафаната."},
    {"venue": "Штарк арена", "city": "Белград", "performer": "Цеца", "starts_at": "2027-01-16T20:00", "price": "36.00", "description": "Цеца на Штарк арена."},
]

DESKS = [
    {"name": "Каса Ялта", "city": "София", "address": "бул. „България“ 1", "operator_name": "Невена Петрова", "venue": "Ялта", "venue_city": "София"},
    {"name": "Каса Център", "city": "София", "address": "ул. „Шишман“ 1", "operator_name": "Георги Димитров", "venue": None, "venue_city": None},
    {"name": "Каса Пловдив", "city": "Пловдив", "address": "ул. „Княз Александър I“ 1", "operator_name": "Иван Колев", "venue": None, "venue_city": None},
    {"name": "Каса Варна", "city": "Варна", "address": "бул. „Княз Борис I“ 65", "operator_name": "Мария Стоянова", "venue": "Планет", "venue_city": "Варна"},
    {"name": "Каса Белград", "city": "Белград", "address": "Цетињска 15", "operator_name": "Јована Илић", "venue": "Драгстор", "venue_city": "Белград"},
]

TICKETS = [
    {"venue": "Ялта", "city": "София", "performer": "Киара", "seat": "A-2", "ticket_type": "student", "buyer": "Мария Георгиева", "desk": "Каса Ялта"},
    {"venue": "Tell Me", "city": "София", "performer": "Галин", "seat": "B-3", "ticket_type": "child", "buyer": "Николай Иванов", "desk": "Каса Център"},
    {"venue": "Купе", "city": "София", "performer": "Селина", "seat": "C-1", "ticket_type": "adult", "buyer": "Елена Димитрова", "desk": "Каса Център"},
    {"venue": "Зала България", "city": "София", "performer": "Ксиор", "seat": "D-5", "ticket_type": "child", "buyer": "Петър Стоянов", "desk": "Каса Център"},
    {"venue": "Петъното", "city": "Пловдив", "performer": "Сис и Джордан", "seat": "A-4", "ticket_type": "student", "buyer": "Иван Петров", "desk": "Каса Пловдив"},
    {"venue": "Планет", "city": "Варна", "performer": "Азис", "seat": "B-2", "ticket_type": "adult", "buyer": "Мария Георгиева", "desk": "Каса Варна"},
    {"venue": "Драгстор", "city": "Белград", "performer": "Цеца", "seat": "A-8", "ticket_type": "student", "buyer": "Јована Илић", "desk": "Каса Белград"},
    {"venue": "Штарк арена", "city": "Белград", "performer": "Цеца", "seat": "E-10", "ticket_type": "child", "buyer": "Николай Иванов", "desk": "Каса Белград"},
    {"venue": "Кръчма При бай Миле", "city": "София", "performer": "Диона", "seat": "F-1", "ticket_type": "adult", "buyer": "Елена Димитрова", "desk": "Каса Център"},
]


def run_seed() -> int:
    with unit_of_work() as session:
        if venue_repo.count(session):
            print("seed: already present", flush=True)
            return 0
    created = 0
    venues = {}
    for row in VENUES:
        saved = venue_service.create_venue(row)
        venues[(saved["name"], saved["city"])] = saved
        created += 1
    events = {}
    for row in EVENTS:
        venue = venues[(row["venue"], row["city"])]
        saved = event_service.create_event(
            {
                "venue_id": venue["id"],
                "performer": row["performer"],
                "starts_at": row["starts_at"],
                "price": row["price"],
                "description": row["description"],
            }
        )
        events[(row["venue"], row["city"], row["performer"])] = saved
        created += 1
    desks = {}
    for row in DESKS:
        payload = {
            "name": row["name"],
            "city": row["city"],
            "address": row["address"],
            "operator_name": row["operator_name"],
        }
        if row["venue"]:
            payload["venue_id"] = venues[(row["venue"], row["venue_city"])]["id"]
        saved = cashdesk_service.create_cashdesk(payload)
        desks[saved["name"]] = saved
        created += 1
    for row in TICKETS:
        event = events[(row["venue"], row["city"], row["performer"])]
        ticket_service.create_ticket(
            {
                "event_id": event["id"],
                "cash_desk_id": desks[row["desk"]]["id"],
                "ticket_type": row["ticket_type"],
                "seat_code": row["seat"],
                "buyer_name": row["buyer"],
                "status": "sold",
            }
        )
        created += 1
    print(f"seed: queued {created}", flush=True)
    return created


def wait_for_journal(expected: int) -> None:
    if expected <= 0:
        return
    deadline = time.time() + 90
    last_print = 0.0
    while time.time() < deadline:
        current = activity_service.count_activity()
        now = time.time()
        if now - last_print > 2:
            print(f"seed: journal {current}/{expected}", flush=True)
            last_print = now
        if current >= expected:
            return
        time.sleep(0.4)
    raise SystemExit(f"seed: journal stuck at {activity_service.count_activity()} expected {expected}")


def main() -> None:
    load_dotenv()
    os.environ["PUBLISH_REQUIRED"] = "1"
    init_db()
    expected = run_seed()
    wait_for_journal(expected)


if __name__ == "__main__":
    main()
