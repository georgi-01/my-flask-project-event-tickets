from datetime import datetime
from decimal import Decimal
from pathlib import Path

from app.formatting import format_datetime, format_price
from app.labels import VENUE_TYPES
from app.parsing import parse_datetime, parse_decimal, parse_seats
from app.seed import DESKS, EVENTS, TICKETS, VENUES


def test_price_and_datetime_formatting():
    assert format_price(Decimal("30")) == "30,00 лв."
    assert format_price("1234.5") == "1 234,50 лв."
    assert format_price(0) == "0,00 лв."
    moment = datetime(2026, 11, 7, 23, 0)
    assert format_datetime(moment) == "7 ноември 2026, 23:00"
    assert parse_decimal("30,00") == Decimal("30.00")
    assert parse_datetime("2026-11-07T23:00") == moment
    assert parse_seats("a-1, A-2") == ["A-1", "A-2"]


def test_seed_covers_the_program():
    venues = {(row["name"], row["city"]): row for row in VENUES}
    bg = [row for row in EVENTS if venues[(row["venue"], row["city"])]["country"] == "България"]
    rs = [row for row in EVENTS if venues[(row["venue"], row["city"])]["country"] == "Сърбия"]
    assert len(bg) == 16
    assert len(rs) == 4
    assert {row["city"] for row in bg} == {"София", "Пловдив", "Варна"}
    assert {row["city"] for row in rs} == {"Белград"}
    names = {row["name"] for row in VENUES}
    for name in ["Ялта", "Tell Me", "Купе", "Петъното", "Строежа", "Cubo", "Планет", "Драгстор"]:
        assert name in names
    assert {row["venue_type"] for row in VENUES} == set(VENUE_TYPES)
    performers = {row["performer"] for row in EVENTS}
    for name in [
        "Киара",
        "Галин",
        "Селина",
        "Мирела",
        "Азис",
        "Силвър",
        "Диона",
        "Ксиор",
        "Сис и Джордан",
        "Цеца",
        "Сека Алексич",
        "Аца Лукас",
    ]:
        assert name in performers
    kupe = venues[("Купе", "София")]
    assert kupe["free_student_entry"] is False
    assert kupe["bottle_discount"] is False
    discounted = [row for row in VENUES if row["free_student_entry"] or row["bottle_discount"]]
    assert discounted
    assert all(row["venue_type"] in {"disco", "club"} for row in discounted)
    assert any(row["free_student_entry"] and row["bottle_discount"] for row in discounted if row["venue_type"] == "disco")
    assert any(row["free_student_entry"] and row["bottle_discount"] for row in discounted if row["venue_type"] == "club")
    assert any(not row["free_student_entry"] for row in VENUES if row["venue_type"] == "disco")
    assert any(not row["free_student_entry"] for row in VENUES if row["venue_type"] == "club")
    assert len(DESKS) >= 4
    assert len(TICKETS) >= 8


def test_stack_files_and_font():
    compose = Path("compose.yaml").read_text(encoding="utf-8")
    nginx = Path("nginx/default.conf").read_text(encoding="utf-8")
    docker = Path("nginx/Dockerfile").read_text(encoding="utf-8")
    css = Path("app/static/css/site.css").read_text(encoding="utf-8")
    assert "8444:443" in compose
    assert "8081:80" in compose
    assert "9998:8080" in compose
    assert "15673:15672" in compose
    assert "web1" in compose and "web2" in compose
    assert "5432:5432" not in compose
    assert "5672:5672" not in compose
    assert "server web1:8000;" in nginx
    assert "server web2:8000;" in nginx
    assert "return 301 https://$host:8444$request_uri;" in nginx
    assert "/CN=localhost" in docker
    assert "Source Sans 3" in css
    for path in Path("app").rglob("*.py"):
        text = path.read_text(encoding="utf-8")
        assert "bileti_dev" not in text
        assert "from sqlalchemy import text" not in text
        assert ".execute(" not in text
        folded = text.casefold()
        assert "кафене" not in folded
        assert "регистър" not in folded
