from flask import (
    Blueprint,
    render_template,
    request
)
from app.db import get_db
from app.db_wrappers import get_tasks, export, get_exports

bp = Blueprint('tasks', __name__)

@bp.route('/tasks', methods=('GET',))
def tasks():
    tasks = get_tasks(get_db())
    return render_template('tasks.html', tasks=tasks)
