import json
import logging
import os
import time

import pika
from dotenv import load_dotenv

from app.db import init_db
from app.errors import ValidationError
from app.events import EXCHANGE, QUEUE, ROUTING_KEY
from app.services.activity import record_activity

log = logging.getLogger("bileti.worker")


def handle_payload(payload: dict) -> None:
    record_activity(payload)


def main() -> None:
    load_dotenv()
    logging.basicConfig(
        level=logging.INFO,
        format="%(asctime)s %(levelname)s %(name)s %(message)s",
    )
    init_db()
    url = os.environ["RABBITMQ_URL"]
    while True:
        try:
            _consume(url)
        except Exception:
            log.exception("worker disconnected")
            time.sleep(3)


def _consume(url: str) -> None:
    params = pika.URLParameters(url)
    params.heartbeat = 30
    params.blocked_connection_timeout = 8
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.exchange_declare(exchange=EXCHANGE, exchange_type="direct", durable=True)
    channel.queue_declare(queue=QUEUE, durable=True)
    channel.queue_bind(exchange=EXCHANGE, queue=QUEUE, routing_key=ROUTING_KEY)
    channel.basic_qos(prefetch_count=1)

    def callback(ch, method, _properties, body):
        try:
            payload = json.loads(body.decode("utf-8"))
        except Exception:
            log.exception("malformed message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        try:
            handle_payload(payload)
        except ValidationError:
            log.exception("rejected message")
            ch.basic_ack(delivery_tag=method.delivery_tag)
            return
        except Exception:
            log.exception("journal write failed")
            time.sleep(2)
            ch.basic_nack(delivery_tag=method.delivery_tag, requeue=True)
            return
        ch.basic_ack(delivery_tag=method.delivery_tag)
        log.info(
            "journal %s %s %s",
            payload.get("action"),
            payload.get("entity"),
            payload.get("entity_id"),
        )

    channel.basic_consume(queue=QUEUE, on_message_callback=callback)
    log.info("worker listening on %s", QUEUE)
    channel.start_consuming()


if __name__ == "__main__":
    main()
