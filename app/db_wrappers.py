import multiprocessing
import json
import os
from unicodedata import name
from app.db import SQLiteJSONEncoder
from flask import current_app
from app.utils import get_named_arguments

"""

All functions that depend on the peculiarities of the database

"""

# EXAMPLES

def add_example(db, prompt_id, completion, tags):
    c = db.cursor()
    c.execute("INSERT INTO examples (completion, prompt_id) VALUES (?, ?)", (completion, prompt_id))
    item_id = c.lastrowid
    
    # Add tags
    for tag in tags:
        c.execute("INSERT INTO tags (example_id, value) VALUES (?, ?)", (item_id, tag))
    db.commit()
    return item_id


def delete_example(db, example_id):
    db.execute("DELETE FROM examples WHERE id = ?", (example_id,))
    db.commit()


def update_example(db, example_id, completion, tags):
    c = db.cursor()

    # Remove all tags
    c.execute("DELETE FROM tags WHERE example_id = ?", (example_id,))
    # Update text
    c.execute("UPDATE examples SET completion = ? WHERE id = ?", (completion, example_id))
    for t in tags:
        c.execute("INSERT INTO tags (example_id, value) VALUES (?, ?)", (example_id, t))
    db.commit()
    return example_id


# PROMPTS

def delete_prompt(db, prompt_id):

    # Remove all tags
    # Remove all prompt_values
    # remove associated examples

    db.execute("DELETE FROM prompts WHERE id = ?", (prompt_id,))
    db.execute("DELETE FROM tags WHERE prompt_id = ?", (prompt_id,))
    db.execute("DELETE FROM prompt_values WHERE prompt_id = ?", (prompt_id,))
    db.execute("DELETE FROM examples WHERE prompt_id = ?", (prompt_id,))
    db.commit()

def update_prompt(db, prompt_id, prompt_values, tags):
    c = db.cursor()

    # Update prompt values
    for key in prompt_values:
        sql = """
            UPDATE prompt_values SET value = ? WHERE prompt_id = ? AND key = ?
        """
        c.execute(sql, (prompt_values[key], prompt_id, key))
    # Update tags
    # Remove all prior tags
    sql = """
        DELETE FROM tags
        WHERE prompt_id = ?
    """
    c.execute(sql, (prompt_id,))
    for tag in tags:
        c.execute("INSERT INTO tags (value, prompt_id) VALUES (?, ?)", (tag, prompt_id))

    db.commit()
    return prompt_id

# Adds prompt to database and returns that prompt's id
def add_prompt(db, **kwargs):

    tags = kwargs['tags']
    keys = kwargs['keys']
    project_id = kwargs['project_id']
    style_id = kwargs['style_id']

    c = db.cursor()

    c.execute("INSERT INTO prompts (project_id, style) VALUES (?, ?)", (project_id, style_id))
    prompt_id = c.lastrowid

    for t in tags:
        c.execute("INSERT INTO tags (value, prompt_id) VALUES (?, ?)", (t, prompt_id))

    for k in keys:
        c.execute("INSERT INTO prompt_values (prompt_id, key, value) VALUES (?, ?, ?)", (prompt_id, k, keys[k]))

    db.commit()
    return prompt_id

# Takes data and inserts prompts and examples
# Data is a list of dictionaries (i.e. json data)
# tags is a list
def add_bulk(db, data, tags, project_id, style_id):
    c = db.cursor()
    sql = """
        INSERT INTO tasks (`type`, `status`)
        VALUES ("bulk_upload",
                "in_progress"
                );
    """
    c.execute(sql)
    task_id = c.lastrowid
    db.commit()

    p = multiprocessing.Process(target=add_bulk_background, args=(db, task_id, data, tags, project_id, style_id))
    p.start()

    sql = """
        UPDATE tasks
        SET pid = ?
        WHERE id = ?
    """
    db.execute(sql, (p.pid, task_id))

    status = {
        'pid': p.pid,
        'status': 'in_progress'
    }
    return status

# NOTE: doesn't support example tags yet or multiple examples per prompt
def add_bulk_background(db, task_id, data, tags, project_id, style_id):
    try:
        c = db.cursor()

        # Get the correct keys and note which is the completion key
        sql = """
            SELECT * FROM style_keys
            WHERE style_id = ?
        """
        res = c.execute(sql, (style_id,))
        style_keys = res.fetchall()

        # Get the style
        sql = """
            SELECT * FROM styles
            WHERE id = ?
        """
        res = c.execute(sql, (style_id))
        style_info = res.fetchone()

        completion_key = style_info['completion_key']

        prompt_values_keys = [x['name'] for x in style_keys if x['name'] != completion_key]
        db.commit()

        for item in data:

            # Add new prompt
            sql = """
                INSERT INTO prompts (style, project_id) VALUES (?, ?)
            """
            c.execute(sql, (style_id, project_id))
            prompt_id = c.lastrowid

            # Add examples and prompt values
            for key in item:
                if key == completion_key:
                    sql = """
                        INSERT INTO examples (prompt_id, completion) VALUES (?, ?)
                    """
                    c.execute(sql, (prompt_id, item[key]))
                elif key in prompt_values_keys:  # need to avoid tags, other irrelevant values
                    sql = """
                        INSERT INTO prompt_values (prompt_id, key, value) VALUES (?, ?, ?)
                    """
                    c.execute(sql, (prompt_id, key, item[key]))

            # Add tags to prompt
            for tag in tags:
                sql = """
                    INSERT INTO tags (prompt_id, value) VALUES (?, ?)
                """
                c.execute(sql, (prompt_id, tag))

            db.commit()

        sql = """
            UPDATE tasks
            SET status = 'completed'
            WHERE id = ?
        """
        db.execute(sql, (task_id,))
        db.commit()
    except:
        sql = """
        UPDATE tasks
        SET status = 'failed'
        WHERE id = ?;
        """
        db.execute(sql, (task_id,))
        db.commit()

"""

Will export a json file, which is a list of dictionaries with each key matching
   a named argument in the template format string.
All named arguments are present in every dictionary.
Does not include tags at the moment.

If filename is None or "", the filename becomes "export.json"

"""
def export(db, filename, tags=[], content="", example="", project_id=None, style_id=None):

    if not filename:
        filename = "export.json"

    c = db.cursor()
    sql = """
        INSERT INTO tasks (`type`, `status`)
        VALUES ("export",
                "in_progress"
                );
    """
    c.execute(sql)
    db.commit()

    task_id = c.lastrowid

    p = multiprocessing.Process(target=export_background, args=(db, task_id, filename, content, tags, example, style_id, project_id))
    p.start()

    sql = """
        UPDATE tasks SET `pid` = ?
        WHERE id = ?
    """
    c.execute(sql, (p.pid, task_id))

    db.commit()
    status = {
        'pid': p.pid,
        'status': 'in_progress'
    }
    return status

def export_background(db, task_id, filename, content, tags, example, style_id, project_id):

    # The try catch is not compehensive
    # There should be an option for the user to check on the program itself (via its pid)
    try:
        if not example:
            example = "%"
        if not content:
            content = "%"

        args = [example]

        tag_query_str = ""
        if tags and len(tags) > 0:
            tag_query_str = f"JOIN tags ON prompts.id = tags.prompt_id AND ("
            for i, tag in enumerate(tags):
                tag_query_str += f"tags.value LIKE ?"
                args.append(tag)
                if i < len(tags) - 1:
                    tag_query_str += " OR "
            tag_query_str += ")"

        args.append(content)

        proj_id_query = ""
        if project_id:
            proj_id_query = "AND prompts.project_id = ?"
            args.append(project_id)

        style_id_query = ""
        if style_id:
            style_id_query = "AND prompts.style = ?"
            args.append(style_id)

        # notice that in string, there is no option to put "LEFT" join on examples
        # this is beacuse we really do only want prompts with examples in this case
        sql = f"""
            SELECT DISTINCT prompts.*, styles.template as template, styles.completion_key as completion_key
            FROM prompts
            JOIN prompt_values ON prompts.id = prompt_values.prompt_id
            JOIN styles ON prompts.style = styles.id AND prompt_values.key = styles.preview_key
            JOIN examples ON prompts.id = examples.prompt_id AND examples.completion LIKE ?
            {tag_query_str}
            WHERE prompt_values.value LIKE ?
            {proj_id_query}
            {style_id_query}
            LIMIT 10
        """
        c = db.cursor()
        res = c.execute(sql, tuple(args))
        prompts = res.fetchall()

        path = os.path.join(current_app.config.get('EXPORTS_PATH'), filename)
        fhand = open(path, 'w')
        fhand.write('[\n')

        encoder = SQLiteJSONEncoder(indent=4)

        for k, prompt in enumerate(prompts):
            sql = """
                SELECT * FROM examples
                WHERE prompt_id = ?
            """
            examples = c.execute(sql, (prompt['id'],)).fetchall()

            sql = """
                SELECT * FROM prompt_values
                WHERE prompt_id = ?
            """
            prompt_values = c.execute(sql, (prompt['id'],)).fetchall()
            prompt_value_kwargs = {x['key']: x['value'] for x in prompt_values}

            template = prompt['template']
            named_args = get_named_arguments(template)

            kwargs = {}
            for arg in named_args:
                if arg in prompt_value_kwargs:
                    kwargs[arg] = prompt_value_kwargs[arg]
                elif arg != prompt['completion_key']:
                    kwargs[arg] = ""

            for i, ex in enumerate(examples):
                kwargs[prompt['completion_key']] = ex['completion']
            
                json_data = encoder.encode(kwargs)

                fhand.write(json_data)

                if i < len(examples) - 1:
                    fhand.write(",\n")
            
            if k < len(prompts) - 1:
                fhand.write(",\n")

        fhand.write(']')
        fhand.close()

        sql = """
                INSERT INTO exports (`filename`)
                VALUES (?);
            """
        db.execute(sql, (filename,))

        sql = """
                    UPDATE tasks
                    SET status = 'completed'
                    WHERE id = ?;
                """
        db.execute(sql, (task_id,))
        db.commit()
    except Exception as e:
        sql = """
            UPDATE tasks
            SET status = 'failed'
            WHERE pid = ?;
        """
        db.execute(sql, (os.getpid(),))
        db.commit()
        print(f"Error occurred: {e}")

def search_prompts(db, limit=None, offset=None, content_arg=None, example_arg=None, tags_arg=None, project_id=None, style_id=None):
    
    offset = 0 if not offset else offset
    limit = 100 if not limit else limit
    content_arg = "%" if not content_arg else "%" + content_arg + "%"
    
    x = "" if example_arg else "LEFT"
    example_arg = "%" if not example_arg else "%" + example_arg + "%"

    args = [example_arg]

    tag_query_str = ""
    if tags_arg and len(tags_arg) > 0:
        tag_query_str = f"JOIN tags ON prompts.id = tags.prompt_id AND ("
        for i, tag in enumerate(tags_arg):
            tag_query_str += f"tags.value LIKE ?"
            args.append(tag)
            if i < len(tags_arg) - 1:
                tag_query_str += " OR "
        tag_query_str += ")"

    args.extend([content_arg])

    proj_id_query = ""
    if project_id:
        proj_id_query = "AND prompts.project_id = ?"
        args.append(project_id)

    style_id_query = ""
    if style_id:
        style_id_query = "AND prompts.style = ?"
        args.append(style_id)

    args.extend([limit, offset])

    sql = f"""
        WITH main_search AS
        (
            SELECT DISTINCT prompts.*, prompt_values.*
            FROM prompts
            JOIN prompt_values ON prompts.id = prompt_values.prompt_id
            JOIN styles ON prompts.style = styles.id AND prompt_values.key = styles.preview_key
            {x} JOIN examples ON prompts.id = examples.prompt_id AND examples.completion LIKE ?
            {tag_query_str}
            WHERE prompt_values.value LIKE ?
            {proj_id_query}
            {style_id_query}
        )
        SELECT main_search.*, GROUP_CONCAT(t.value) AS tags, COUNT(*) OVER() AS total_results
        FROM main_search
        LEFT JOIN tags t ON main_search.prompt_id = t.prompt_id
        GROUP BY main_search.id
        LIMIT ?
        OFFSET ?
    """

    results = db.execute(sql, tuple(args))
    fetched = results.fetchall()
    total_results = 0 if len(fetched) == 0 else fetched[0]['total_results']
    return fetched, total_results


def get_tasks(db):
    sql = """
        SELECT * FROM tasks ORDER BY created_at DESC
    """
    tasks = db.execute(sql)
    return tasks

def get_exports(db):
    sql = """
        SELECT * FROM exports ORDER BY created_at DESC
    """
    exports = db.execute(sql)
    return exports

def get_export_by_id(db, id):
    sql = """
        SELECT * FROM exports WHERE id = ?
    """
    export = db.execute(sql, id)
    return export.fetchone()

def get_prompt_by_id(db, id):
    sql = """
        SELECT * FROM prompts WHERE id = ?
    """
    prompt = db.execute(sql, (id,))
    return prompt.fetchone()

def get_examples_by_prompt_id(db, prompt_id, with_tags=True):
    if with_tags:
        sql = """
        SELECT e.*, GROUP_CONCAT(t.value) AS tags
        FROM examples e
        LEFT JOIN tags t ON e.id = t.example_id
        WHERE e.prompt_id = ?
        GROUP BY e.id
        """
    else:
        sql = """
            SELECT * FROM examples WHERE prompt_id = ?
        """
    examples = db.execute(sql, (prompt_id,))
    return examples.fetchall()

def get_projects(db):
    sql = """
        SELECT * FROM projects ORDER BY created_at DESC
    """
    examples = db.execute(sql)
    return examples.fetchall()

def get_project_by_id(db, id):
    sql = """
        SELECT * FROM projects WHERE id = ?
    """
    examples = db.execute(sql, (id,))
    return examples.fetchone()

def get_styles_by_project_id(db, id):
    sql = """
        SELECT * FROM styles WHERE project_id = ?
    """
    examples = db.execute(sql, (id,))
    return examples.fetchall()

def get_styles(db):
    sql = """
        SELECT * FROM styles ORDER BY created_at DESC
    """
    styles = db.execute(sql)
    return styles.fetchall()

def get_style_by_id(db, id):
    sql = """
        SELECT * FROM styles WHERE id = ?
    """
    style = db.execute(sql, (id,))
    return style.fetchone()

def get_keys_by_style_id(db, id):
    sql = """
        SELECT * FROM style_keys WHERE style_id = ?
    """
    keys = db.execute(sql, (id,))
    return keys.fetchall()

def get_tags_by_prompt_id(db, prompt_id):
    sql = """
        SELECT * FROM tags WHERE prompt_id = ?
    """
    tags = db.execute(sql, (prompt_id,))
    return tags.fetchall()

def get_prompt_values_by_prompt_id(db, prompt_id):
    sql = """
        SELECT * FROM prompt_values WHERE prompt_id = ?
    """
    vals = db.execute(sql, (prompt_id,))
    return vals.fetchall()

def add_project(db, name, description):
    sql = """
        INSERT INTO projects (name, desc)
        VALUES (?, ?)
    """
    c = db.cursor()
    c.execute(sql, (name, description))
    proj_id = c.lastrowid
    db.commit()
    return proj_id

def add_style(db, idtext, format_string, completion_key, preview_key, project_id, style_keys):
    sql = """
        INSERT INTO styles (id_text, template, completion_key, preview_key, project_id)
        VALUES (?, ?, ?, ?, ?)
    """
    c = db.cursor()
    c.execute(sql, (idtext, format_string, completion_key, preview_key, project_id))
    style_id = c.lastrowid
    db.commit()

    # Now add style keys
    for key in style_keys:
        sql = """
            INSERT INTO style_keys (name, style_id)
            VALUES (?, ?)
        """
        c.execute(sql, (key, style_id))
    db.commit()

    return style_id
