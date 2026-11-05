from flask import Blueprint

bp = Blueprint("pages", __name__)

from app.pages import activity, cashdesks, program, tickets, venues  # noqa: E402,F401
