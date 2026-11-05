import json
import logging
import os
import time
import uuid

import pika

log = logging.getLogger("bileti.events")

EXCHANGE = "bileti"
QUEUE = "bileti.journal"
ROUTING_KEY = "journal"

_state = {"connection": None, "channel": None}


def build_message(action: str, entity: str, entity_id: int, summary: str) -> dict:
    return {
        "message_id": str(uuid.uuid4()),
        "action": action,
        "entity": entity,
        "entity_id": int(entity_id),
        "summary": summary,
    }


def publish(message: dict) -> None:
    if os.environ.get("TESTING") == "1":
        return
    last = None
    for attempt in range(8):
        try:
            _publish_once(message)
            return
        except Exception as exc:
            last = exc
            _reset()
            time.sleep(0.5 * (attempt + 1))
    log.error("publish failed: %s", last)
    if os.environ.get("PUBLISH_REQUIRED") == "1":
        raise RuntimeError("RabbitMQ publish failed") from last


def _reset() -> None:
    connection = _state.get("connection")
    _state["connection"] = None
    _state["channel"] = None
    if connection is not None and connection.is_open:
        try:
            connection.close()
        except Exception:
            log.debug("rabbit connection close failed", exc_info=True)


def _channel():
    connection = _state.get("connection")
    channel = _state.get("channel")
    if connection is not None and connection.is_open and channel is not None and channel.is_open:
        return channel
    params = pika.URLParameters(os.environ["RABBITMQ_URL"])
    params.heartbeat = 30
    params.blocked_connection_timeout = 8
    params.socket_timeout = 8
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    _state["connection"] = connection
    _state["channel"] = channel
    return channel


def _publish_once(message: dict) -> None:
    channel = _channel()
    channel.basic_publish(
        exchange=EXCHANGE,
        routing_key=ROUTING_KEY,
        body=json.dumps(message, ensure_ascii=False).encode("utf-8"),
        properties=pika.BasicProperties(delivery_mode=2, content_type="application/json"),
    )
