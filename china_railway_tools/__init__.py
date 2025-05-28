from .scrpits import init_script
import logging

logger = logging.getLogger(__name__)


def init_app():
    init_script.run()


init_app()
