from flask import (
    Blueprint,
    render_template,
    request,
    redirect
)
from app.db import get_db
from app.db_wrappers import delete_style, get_project_by_id, get_style_by_id, get_keys_by_style_id, update_style
from app.utils import get_named_arguments
import json

bp = Blueprint('style', __name__)

@bp.route('/style', methods=('GET', 'POST'))
def style():

    errors = []

    db = get_db()
    if request.method == "POST":
        style_id = request.form.get('style_id')
        form_type = request.form.get('form_type')
        if form_type == "update":
            template = request.form.get('template')
            id_text = request.form.get('id_text')
            completion_key = request.form.get('completion_key')
            preview_key = request.form.get('preview_key')

            keys = get_named_arguments(template)
            if preview_key not in keys:
                errors.append("Preview key must be in template")
            if completion_key not in keys:
                errors.append("Completion key must be in template")

            if len(errors) == 0:
                update_style(db, style_id, id_text, template, completion_key, preview_key)
        elif form_type == 'delete':
            if style_id:
                delete_style(db, style_id)


    id = request.args.get('id')

    if not id:
        return redirect("/projects")

    style = get_style_by_id(db, id)
    proj_id = style['project_id']
    project = get_project_by_id(db, proj_id)

    keys = get_keys_by_style_id(db, id)

    return render_template('style.html', style=style, project=project, keys=keys, errors=errors)
