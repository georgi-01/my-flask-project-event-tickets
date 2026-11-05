# Билетница

## Старт

```bash
./install.sh
```

```bash
cp .env.example .env
docker compose up --build -d
docker compose ps
docker compose logs -f web1 worker nginx
docker compose down
docker compose down -v
```

## Адреси

- https://localhost:8444
- http://localhost:8081
- http://localhost:9998
- http://localhost:15673

## Тестове

```bash
python3 -m venv .venv
. .venv/bin/activate
pip install -r requirements-dev.txt
pytest
```

## psql

```bash
docker compose exec db psql -U bileti -d bileti
docker compose exec db psql -U bileti -d bileti -c '\dt'
```

## curl

```bash
curl -k https://localhost:8444/api/events
curl -k https://localhost:8444/api/venues
curl -k https://localhost:8444/api/tickets
curl -k https://localhost:8444/api/cash-desks
curl -k https://localhost:8444/api/activity
```

```bash
curl -k -X POST https://localhost:8444/api/venues \
  -H 'Content-Type: application/json' \
  -d '{"name":"Ялта","venue_type":"disco","city":"София","address":"бул. България 1","country":"България","free_student_entry":true,"bottle_discount":true,"description":"Дискотека."}'
```

```bash
curl -k -X POST https://localhost:8444/api/events \
  -H 'Content-Type: application/json' \
  -d '{"venue_id":1,"performer":"Киара","starts_at":"2026-11-07T23:00","price":"15.00","description":"Нощ с Киара."}'
```

```bash
curl -k -X POST https://localhost:8444/api/cash-desks \
  -H 'Content-Type: application/json' \
  -d '{"name":"Каса Център","city":"София","address":"ул. Шишман 1","operator_name":"Мария Иванова"}'
```

```bash
curl -k -X POST https://localhost:8444/api/tickets \
  -H 'Content-Type: application/json' \
  -d '{"event_id":1,"cash_desk_id":1,"ticket_type":"adult","seat_code":"A-1","buyer_name":"Иван Петров","status":"sold"}'
```

```bash
curl -k -X PUT https://localhost:8444/api/tickets/1 \
  -H 'Content-Type: application/json' \
  -d '{"event_id":1,"cash_desk_id":1,"ticket_type":"adult","seat_code":"A-1","buyer_name":"Мария Георгиева","status":"sold"}'
```

```bash
curl -k -X DELETE https://localhost:8444/api/tickets/1
```

## Опашка

```bash
docker compose exec rabbitmq rabbitmqctl list_queues
```
