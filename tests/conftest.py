import os
import tempfile

import pytest

fd, DB_PATH = tempfile.mkstemp(prefix="bileti-", suffix=".sqlite")
os.close(fd)
os.environ["DATABASE_URL"] = f"sqlite+pysqlite:///{DB_PATH}"
os.environ["TESTING"] = "1"
os.environ["SECRET_KEY"] = "testing"
os.environ["RABBITMQ_URL"] = "amqp://guest:guest@localhost:5672/%2F"


@pytest.fixture(scope="session")
def app():
    from app import create_app
    from app.db import reset_db

    application = create_app()
    yield application
    reset_db()


@pytest.fixture
def client(app):
    from app.db import engine
    from app.models import Base

    Base.metadata.drop_all(engine)
    Base.metadata.create_all(engine)
    return app.test_client()


@pytest.fixture(scope="session", autouse=True)
def _cleanup_db():
    yield
    from app.db import reset_db

    reset_db()
    if os.path.exists(DB_PATH):
        os.remove(DB_PATH)
