from tests.helpers import make_desk, make_event, make_venue, ticket_payload


def test_health(client):
    response = client.get("/health")
    assert response.status_code == 200
    assert response.get_json()["status"] == "ok"


def test_venue_crud(client):
    created = make_venue(client)
    assert created["venue_type_label"] == "дискотека"
    listed = client.get("/api/venues").get_json()
    assert listed[0]["name"] == "Ялта"
    updated = client.put(
        f"/api/venues/{created['id']}",
        json={
            "name": "Ялта",
            "venue_type": "disco",
            "city": "София",
            "address": "бул. „Витоша“ 10",
            "country": "България",
            "free_student_entry": True,
            "bottle_discount": False,
            "description": "Нов адрес.",
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["address"] == "бул. „Витоша“ 10"
    assert updated.get_json()["bottle_discount"] is False
    deleted = client.delete(f"/api/venues/{created['id']}")
    assert deleted.status_code == 204
    assert deleted.get_data() == b""
    assert client.get(f"/api/venues/{created['id']}").status_code == 404


def test_bar_rejects_discounts(client):
    response = client.post(
        "/api/venues",
        json={
            "name": "Спутник",
            "venue_type": "bar",
            "city": "София",
            "address": "ул. „Шишман“ 22",
            "country": "България",
            "free_student_entry": True,
            "bottle_discount": False,
        },
    )
    assert response.status_code == 400
    assert "Отстъпките" in response.get_json()["error"]


def test_event_crud_and_missing_venue(client):
    missing = client.post(
        "/api/events",
        json={
            "venue_id": 99,
            "performer": "Киара",
            "starts_at": "2026-11-07T23:00",
            "price": "30,00",
        },
    )
    assert missing.status_code == 400
    venue = make_venue(client)
    event = make_event(client, venue)
    assert event["performer"] == "Киара"
    assert event["price"] == "30.00"
    assert event["student_price"] == "0.00"
    assert event["child_price"] is None
    renamed = client.put(
        f"/api/events/{event['id']}",
        json={
            "venue_id": venue["id"],
            "performer": "Галин",
            "starts_at": "2026-11-08T22:30",
            "price": "35.00",
            "description": "Клубна вечер.",
        },
    )
    assert renamed.status_code == 200
    assert renamed.get_json()["performer"] == "Галин"
    assert client.delete(f"/api/events/{event['id']}").status_code == 204
    assert client.get(f"/api/events/{event['id']}").status_code == 404


def test_cash_desk_crud(client):
    created = make_desk(client)
    assert created["operator_name"] == "Мария Иванова"
    updated = client.put(
        f"/api/cash-desks/{created['id']}",
        json={
            "name": "Каса Център",
            "city": "Пловдив",
            "address": "ул. „Княз Александър I“ 1",
            "operator_name": "Иван Колев",
        },
    )
    assert updated.status_code == 200
    assert updated.get_json()["city"] == "Пловдив"
    assert client.delete(f"/api/cash-desks/{created['id']}").status_code == 204
    assert client.get("/api/cash-desks").get_json() == []


def test_adult_student_and_child_prices(client):
    disco = make_venue(client)
    event = make_event(client, disco)
    desk = make_desk(client)
    adult = client.post("/api/tickets", json=ticket_payload(event, desk))
    assert adult.status_code == 201
    assert adult.get_json()["price"] == "30.00"
    student = client.post(
        "/api/tickets",
        json=ticket_payload(event, desk, ticket_type="student", seat_code="A-2", buyer_name="Мария Георгиева"),
    )
    assert student.status_code == 201
    assert student.get_json()["price"] == "0.00"
    child = client.post(
        "/api/tickets",
        json=ticket_payload(event, desk, ticket_type="child", seat_code="A-3"),
    )
    assert child.status_code == 400
    assert "дискотека" in child.get_json()["error"]


def test_student_hidden_rule_and_half_child_price(client):
    venue = make_venue(
        client,
        name="Спутник",
        venue_type="bar",
        free_student_entry=False,
        bottle_discount=False,
    )
    event = make_event(client, venue, performer="Азис", price="25.00", starts_at="2026-11-15T21:00")
    assert event["student_price"] is None
    assert event["child_price"] == "12.50"
    desk = make_desk(client)
    rejected = client.post(
        "/api/tickets",
        json=ticket_payload(event, desk, ticket_type="student"),
    )
    assert rejected.status_code == 400
    sold = client.post(
        "/api/tickets",
        json=ticket_payload(event, desk, ticket_type="child", buyer_name="Петър Стоянов"),
    )
    assert sold.status_code == 201
    assert sold.get_json()["price"] == "12.50"


def test_duplicate_seat_and_ticket_update_delete(client):
    venue = make_venue(client, name="Купе", free_student_entry=False, bottle_discount=False)
    event = make_event(client, venue, performer="Селина", starts_at="2026-11-13T23:30")
    desk = make_desk(client)
    first = client.post("/api/tickets", json=ticket_payload(event, desk, seat_code="C-1"))
    assert first.status_code == 201
    ticket_id = first.get_json()["id"]
    again = client.post("/api/tickets", json=ticket_payload(event, desk, seat_code="C-1", buyer_name="Елена Димитрова"))
    assert again.status_code == 409
    changed = client.put(
        f"/api/tickets/{ticket_id}",
        json=ticket_payload(event, desk, seat_code="C-2", buyer_name="Елена Димитрова", status="reserved"),
    )
    assert changed.status_code == 200
    assert changed.get_json()["seat_code"] == "C-2"
    assert changed.get_json()["status"] == "reserved"
    assert client.delete(f"/api/tickets/{ticket_id}").status_code == 204
    assert client.get("/api/tickets").get_json() == []


def test_desk_with_tickets_cannot_be_deleted(client):
    venue = make_venue(client)
    event = make_event(client, venue)
    desk = make_desk(client, name="Каса Ялта")
    assert client.post("/api/tickets", json=ticket_payload(event, desk)).status_code == 201
    response = client.delete(f"/api/cash-desks/{desk['id']}")
    assert response.status_code == 409


def test_journal_survives_parent_delete(client):
    from app.events import build_message
    from app.services.activity import record_activity

    venue = make_venue(client)
    event = make_event(client, venue)
    message = build_message("created", "event", event["id"], "Създадено събитие: Киара — Ялта")
    assert record_activity(message)["entity_id"] == event["id"]
    assert record_activity(message) is None
    assert client.delete(f"/api/venues/{venue['id']}").status_code == 204
    assert client.get(f"/api/events/{event['id']}").status_code == 404
    rows = client.get("/api/activity").get_json()
    assert len(rows) == 1
    assert rows[0]["summary"] == "Създадено събитие: Киара — Ялта"
    assert client.get(f"/api/activity/{rows[0]['id']}").status_code == 200


def test_bad_json_and_event_search(client):
    assert client.post("/api/venues", data="nope", content_type="application/json").status_code == 400
    venue = make_venue(client)
    other = make_venue(
        client,
        name="Планет",
        city="Варна",
        venue_type="disco",
        address="бул. „Княз Борис I“ 65",
    )
    make_event(client, venue, performer="Киара")
    make_event(client, other, performer="Азис", starts_at="2026-12-12T23:00", price="28.00")
    found = client.get("/api/events?q=киара").get_json()
    assert len(found) == 1
    assert found[0]["venue_name"] == "Ялта"
    by_city = client.get("/api/events?city=Варна").get_json()
    assert [row["performer"] for row in by_city] == ["Азис"]
    by_date = client.get("/api/events?date=2026-12-12").get_json()
    assert [row["performer"] for row in by_date] == ["Азис"]
    assert client.get("/api/events?date=nope").status_code == 400
