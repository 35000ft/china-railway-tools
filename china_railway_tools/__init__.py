from .database.schema import init_db
from .scrpits import init_script


def init_app():
    init_db()
    init_script.run()


init_app()
