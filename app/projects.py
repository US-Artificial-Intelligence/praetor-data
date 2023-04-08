from flask import (
    Blueprint,
    render_template,
    request,
    redirect
)
from app.db import get_db
from app.db_wrappers import delete_project, get_projects, get_project_by_id, get_styles_by_project_id, add_project, add_style, delete_project
from app.utils import get_named_arguments

bp = Blueprint('projects', __name__)

@bp.route('/projects', methods=('GET', 'POST'))
def projects():

    if request.method == "POST":
        name = request.form.get('name')
        description = request.form.get('description')
        add_project(get_db(), name, description)

    projects = get_projects(get_db())
    return render_template('projects.html', projects=projects)

@bp.route('/project', methods=('GET', 'POST'))
def project():

    db = get_db()

    errors = []

    if request.method == 'POST':
        project_id = request.form.get('project_id')
        idtext = request.form.get('id_text')
        format_string = request.form.get('format_string')
        completion_key = request.form.get('completion_key')
        preview_key = request.form.get('preview_key')

        # If there's no other args besides id, assume the request means delete
        if not idtext and not format_string and not completion_key and not preview_key:
            if project_id:
                delete_project(db, project_id)
            # if there's no project id either, we'll just redirect the user back to projects
            
        else:
            style_keys = get_named_arguments(format_string)

            # In the future, should throw errors when completion/preview key not in style_keys
            if completion_key not in style_keys:
                errors.append("Completion key not in the format string")
            elif preview_key not in style_keys:
                errors.append("Preview key not in the format string")
            else:
                add_style(db, idtext, format_string, completion_key, preview_key, project_id, style_keys)

    project_id = request.args.get("id")

    if not project_id:
        return redirect('/projects')

    project = get_project_by_id(get_db(), project_id)
    styles = get_styles_by_project_id(get_db(), project_id)
    return render_template('project.html', project=project, styles=styles, errors=errors)
