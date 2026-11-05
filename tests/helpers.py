def make_venue(client, **overrides):
    payload = {
        "name": "Ялта",
        "venue_type": "disco",
        "city": "София",
        "address": "бул. „България“ 1",
        "country": "България",
        "free_student_entry": True,
        "bottle_discount": True,
        "description": "Дискотека.",
    }
    payload.update(overrides)
    response = client.post("/api/venues", json=payload)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def make_event(client, venue, **overrides):
    payload = {
        "venue_id": venue["id"],
        "performer": "Киара",
        "starts_at": "2026-11-07T23:00",
        "adult_price": "30.00",
        "description": "Нощ с Киара.",
    }
    payload.update(overrides)
    response = client.post("/api/events", json=payload)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def make_desk(client, **overrides):
    payload = {
        "name": "Каса Център",
        "city": "София",
        "address": "ул. „Шишман“ 1",
        "operator_name": "Мария Иванова",
    }
    payload.update(overrides)
    response = client.post("/api/cash-desks", json=payload)
    assert response.status_code == 201, response.get_data(as_text=True)
    return response.get_json()


def ticket_payload(event, desk, **overrides):
    payload = {
        "event_id": event["id"],
        "cash_desk_id": desk["id"],
        "ticket_type": "adult",
        "seat_code": "A-1",
        "buyer_name": "Иван Петров",
        "status": "sold",
    }
    payload.update(overrides)
    return payload
