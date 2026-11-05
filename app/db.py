import os
from contextlib import contextmanager

from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy.pool import NullPool

engine = None
Session = None


def init_db():
    global engine, Session
    if engine is not None:
        return engine
    url = os.environ.get("DATABASE_URL")
    if not url:
        raise RuntimeError("DATABASE_URL is not set")
    kwargs = {"pool_pre_ping": True}
    if url.startswith("sqlite"):
        kwargs["connect_args"] = {"check_same_thread": False}
        kwargs["poolclass"] = NullPool
    engine = create_engine(url, **kwargs)
    Session = sessionmaker(bind=engine, expire_on_commit=False)
    from app.models import Base

    Base.metadata.create_all(engine)
    return engine


def reset_db():
    global engine, Session
    if engine is not None:
        engine.dispose()
    engine = None
    Session = None


@contextmanager
def unit_of_work():
    if Session is None:
        init_db()
    session = Session()
    try:
        yield session
        session.commit()
    except Exception:
        session.rollback()
        raise
    finally:
        session.close()
