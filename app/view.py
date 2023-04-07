from flask import (
    Blueprint,
    redirect,
    render_template,
    request
)
from app.db import get_db
from app.db_wrappers import add_example, delete_example, update_example, get_examples_by_prompt_id, get_prompt_by_id, get_prompt_values_by_prompt_id, get_style_by_id, get_tags_by_prompt_id, update_prompt, delete_prompt
from app.utils import tag_string_to_list

bp = Blueprint('view', __name__)

@bp.route('/view', methods=('GET', 'POST'))
def view():

    prompt_id = request.args.get("prompt_id")

    db = get_db()

    if request.method == "POST":

        update_type = request.form.get("update_type")

        if update_type == "update_prompt":
            new_prompt_values = {}
            for key, value in request.form.items():
                if key.find("key.") == 0:
                    new_prompt_values[key[4:]] = value
            tags = request.form.get("tags")
            tags = tag_string_to_list(tags)
            update_prompt(db, prompt_id, new_prompt_values, tags)
        elif update_type == "delete_prompt":
            delete_prompt(db, prompt_id)
        elif update_type == "add_completion":
            completion = request.form.get("completion")
            tags = request.form.get("tags")
            tags = tag_string_to_list(tags)
            add_example(db, prompt_id, completion, tags)
        elif update_type == "update_completion":
            example_id = request.form.get("id")
            completion = request.form.get("completion")
            tags = request.form.get("tags")
            tags = tag_string_to_list(tags)
            update_example(db, example_id, completion, tags)
        elif update_type == "delete_completion":
            example_id = request.form.get("id")
            delete_example(db, example_id)

    prompt_dict = get_prompt_by_id(db, prompt_id)
    tags = None
    prompt_values = None
    completions = None
    style = None
    tags_str = None
    if prompt_dict:
        tags = get_tags_by_prompt_id(db, prompt_id)
        tags_str = ",".join([tag['value'] for tag in tags])

        prompt_values = get_prompt_values_by_prompt_id(db, prompt_id)
        style = get_style_by_id(db, prompt_dict['style'])

        completions = get_examples_by_prompt_id(db, prompt_id, with_tags=True)

    return render_template('view.html', prompt=prompt_dict, style=style, prompt_values=prompt_values, prompt_tags=tags_str, completions=completions)