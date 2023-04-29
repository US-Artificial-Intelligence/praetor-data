from flask import (
    Blueprint,
    render_template,
    request
)
from app.db import get_db
from app.db_wrappers import delete_project, get_projects, search_prompts, get_styles, delete_prompt
from app.utils import tag_string_to_list
import json

bp = Blueprint('home', __name__)

@bp.route('/', methods=('GET',))
def home(): 
    return render_template('home.html')


@bp.route('/manifest', methods=('GET', 'POST'))
def manifest():

    db = get_db()

    # When a user selects prompts via check box and clicks a button
    # This will trigger a special json response, not the web page
    if request.method == 'POST':
        form_data = request.json
        selected_prompts = form_data['prompt_ids']
        action = form_data['action']
        if action == 'delete':
            # One day, this should probably be batched
            for prompt_id in selected_prompts:
                delete_prompt(db, prompt_id)
        response_text = json.dumps({'response': 'success', 'prompts_affected': selected_prompts, 'action': action})
        return response_text

    limit = 100
    offset = request.args.get('offset')
    if not offset:
        offset = 0

    content_arg = request.args.get("content")
    example_arg = request.args.get("example")
    tags_arg = request.args.get("tags")
    tags_arg = tag_string_to_list(tags_arg)
    project_id_arg = request.args.get("project_id")
    if project_id_arg == "":
        project_id_arg = None
    style_id_arg = request.args.get("style_id")
    if style_id_arg == "":
        style_id_arg = None

    projects = get_projects(db)
    styles = get_styles(db)

    prompts, total_results = search_prompts(db, limit, offset, content_arg, example_arg, tags_arg, project_id_arg, style_id_arg)

    return render_template('manifest.html', prompts=prompts, page_size=limit, total_results=total_results, projects=projects, styles=styles)
