import os

from flask import Flask


def create_app(test_config=None):
    # create and configure the app
    app = Flask(__name__, instance_relative_config=True)
    app.config.from_mapping(
        SECRET_KEY='dev',
        DATABASE=os.path.join(app.instance_path, 'app.sqlite'),
        EXPORTS_PATH=os.path.join(app.instance_path, 'exports')
    )

    if test_config is None:
        # load the instance config, if it exists, when not testing
        app.config.from_pyfile('config.py', silent=True)
    else:
        # load the test config if passed in
        app.config.from_mapping(test_config)

    # ensure the instance folder exists
    try:
        os.makedirs(app.instance_path)
    except OSError:
        pass
    try:
        os.makedirs(os.path.join(app.instance_path, 'exports'))
    except OSError:
        pass

    from . import view
    app.register_blueprint(view.bp)

    from . import home
    app.register_blueprint(home.bp)

    from . import add
    app.register_blueprint(add.bp)

    from . import tasks
    app.register_blueprint(tasks.bp)

    from . import exporting
    app.register_blueprint(exporting.bp)

    from . import projects
    app.register_blueprint(projects.bp)

    from . import style
    app.register_blueprint(style.bp)

    # connect database
    from . import db
    db.init_app(app)

    return app
