from flask import (
    Blueprint,
    render_template,
    request
)
from app.db import get_db
from app.db_wrappers import get_project_by_id, get_style_by_id, get_keys_by_style_id
import json

bp = Blueprint('style', __name__)

@bp.route('/style', methods=('GET',))
def style():
    id = request.args.get('id')
    style = get_style_by_id(get_db(), id)
    proj_id = style['project_id']
    project = get_project_by_id(get_db(), proj_id)

    keys = get_keys_by_style_id(get_db(), id)
    print(keys)

    return render_template('style.html', style=style, project=project, keys=keys)
