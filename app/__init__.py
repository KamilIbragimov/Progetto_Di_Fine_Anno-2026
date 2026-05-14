"""Application factory: crea l'app Flask, registra i blueprint, inizializza il DB."""
import os
from flask import Flask, render_template
from .db import init_app as init_db
from . import auth, main, studenti, docenti


def create_app():
    app = Flask(__name__, instance_relative_config=True)

    app.config.from_mapping(
        SECRET_KEY=os.environ.get('SECRET_KEY', 'dev'),
        DATABASE=os.path.join(app.instance_path, 'schoolhrm.sqlite'),
        SESSION_PERMANENT=False,
    )

    os.makedirs(app.instance_path, exist_ok=True)

    init_db(app)

    app.register_blueprint(auth.bp)
    app.register_blueprint(main.bp)
    app.register_blueprint(studenti.bp)
    app.register_blueprint(docenti.bp)

    @app.errorhandler(404)
    def not_found(e):
        return render_template('404.html'), 404

    @app.errorhandler(403)
    def forbidden(e):
        return render_template('404.html'), 403

    return app
