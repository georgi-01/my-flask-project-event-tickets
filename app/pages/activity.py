from flask import render_template

from app.pages import bp
from app.services import activity as activity_service


@bp.get("/activity")
def activity_list():
    return render_template("activity_list.html", rows=activity_service.list_activity())
