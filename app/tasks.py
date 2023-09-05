from flask import (
    Blueprint,
    render_template,
    request
)
from app.db import get_db
from app.db_wrappers import get_tasks, check_running

bp = Blueprint('tasks', __name__)

@bp.route('/tasks', methods=('GET',))
def tasks():
    db = get_db()
    check_running(db)
    tasks = get_tasks(db)
    return render_template('tasks.html', tasks=tasks)
