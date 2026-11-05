from tests.helpers import make_desk, make_event, make_venue


def test_home_copy_and_footer(client):
    html = client.get("/").get_data(as_text=True)
    assert "Билетница" in html
    assert "Flask и Gunicorn · PostgreSQL · Nginx · RabbitMQ · worker · Dozzle" in html
    assert "Филтри" in html
    assert "Програма" in html
    assert "Билети" in html
    assert "Каси" in html
    assert "Активност" in html
    assert "регистър" not in html.casefold()
    assert "кафене" not in html.casefold()
    assert "реплики" in html
    assert "self-signed" in html
    assert "Dozzle :9998" in html
    assert 'id="filter-panel"' in html
    assert 'class="filter-panel" hidden' in html


def test_program_card_and_purchase(client):
    venue = make_venue(client)
    event = make_event(client, venue)
    desk = make_desk(client)
    home = client.get("/").get_data(as_text=True)
    assert "Ялта" in home
    assert "Киара" in home
    assert "Студенти безплатно" in home
    detail = client.get(f"/events/{event['id']}")
    assert detail.status_code == 200
    page = detail.get_data(as_text=True)
    assert "Студент" in page
    assert "Дете" not in page
    assert "Възрастен" in page
    bought = client.post(
        f"/events/{event['id']}/buy",
        data={
            "ticket_type": "adult",
            "seats": "B-1, B-2",
            "buyer_name": "Иван Петров",
            "cash_desk_id": desk["id"],
        },
        follow_redirects=True,
    )
    assert bought.status_code == 200
    assert "Билетите са закупени." in bought.get_data(as_text=True)
    tickets = client.get("/api/tickets").get_json()
    assert sorted(ticket["seat_code"] for ticket in tickets) == ["B-1", "B-2"]


def test_ticket_buttons_follow_venue_rules(client):
    kupe = make_venue(client, name="Купе", free_student_entry=False, bottle_discount=False)
    bar = make_venue(
        client,
        name="Спутник",
        venue_type="bar",
        free_student_entry=False,
        bottle_discount=False,
        address="ул. „Шишман“ 22",
    )
    club = make_venue(
        client,
        name="Tell Me",
        venue_type="club",
        city="София",
        address="Студентски град",
    )
    kupe_event = make_event(client, kupe, performer="Селина", starts_at="2026-11-13T23:30")
    bar_event = make_event(client, bar, performer="Азис", starts_at="2026-11-15T21:00")
    club_event = make_event(client, club, performer="Галин", starts_at="2026-11-08T22:30")
    kupe_html = client.get(f"/events/{kupe_event['id']}").get_data(as_text=True)
    bar_html = client.get(f"/events/{bar_event['id']}").get_data(as_text=True)
    club_html = client.get(f"/events/{club_event['id']}").get_data(as_text=True)
    assert "Студент" not in kupe_html
    assert "Дете" not in kupe_html
    assert "Възрастен" in kupe_html
    assert "−50% бутилка" not in kupe_html
    assert "Студент" not in bar_html
    assert "Дете" in bar_html
    assert "Студент" in club_html
    assert "Дете" in club_html


def test_ticket_form_follows_event_rules(client):
    disco = make_venue(client, name="Ялта")
    bar = make_venue(
        client,
        name="Спутник",
        venue_type="bar",
        free_student_entry=False,
        bottle_discount=False,
        address="ул. „Шишман“ 22",
    )
    make_event(client, disco, performer="Киара", starts_at="2026-11-07T23:00")
    make_event(client, bar, performer="Азис", starts_at="2026-11-15T21:00", price="13.00")
    html = client.get("/tickets/new").get_data(as_text=True)
    assert 'data-student="1"' in html
    assert 'data-student="0"' in html
    assert 'data-child="0"' in html
    assert 'data-child="1"' in html
    detail = client.get("/events/1").get_data(as_text=True)
    assert "30,00 €" in detail


def test_form_pages_and_missing(client):
    venue_form = client.get("/venues/new").get_data(as_text=True)
    assert 'placeholder="напр. Ялта"' in venue_form
    assert "<span class=\"star\">*</span>" in venue_form
    created = client.post(
        "/venues",
        data={
            "name": "Планет",
            "venue_type": "disco",
            "city": "Варна",
            "address": "бул. „Княз Борис I“ 65",
            "country": "България",
            "description": "Дискотека.",
            "free_student_entry": "1",
            "bottle_discount": "1",
        },
        follow_redirects=True,
    )
    assert created.status_code == 200
    assert "Планет" in created.get_data(as_text=True)
    assert client.get("/tickets").status_code == 200
    assert client.get("/cash-desks").status_code == 200
    assert client.get("/activity").status_code == 200
    missing = client.get("/no-such")
    assert missing.status_code == 404
    assert "Страницата не е намерена." in missing.get_data(as_text=True)
    assert client.get("/api/no-such").status_code == 404
