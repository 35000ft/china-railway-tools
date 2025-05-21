# config.py
import os
from appdirs import user_data_dir

from china_railway_tools.schemas.AppConifg import AppConfig

APP_NAME = "CR_TOOLS"
APP_AUTHOR = "yunshang"
DEFAULT_DB_PATH = os.getenv("CR_TOOLS_DATABASE_PATH", os.path.join(user_data_dir(APP_NAME, APP_AUTHOR), 'data.db'))

PERSONAL_CONFIG = {

}


def get_default_db_url():
    if not os.path.exists(os.path.dirname(DEFAULT_DB_PATH)):
        os.makedirs(os.path.dirname(DEFAULT_DB_PATH))
    return f"sqlite:///{DEFAULT_DB_PATH}"


SQLALCHEMY_DATABASE_URL = get_default_db_url()


def set_config(config: AppConfig):
    global PERSONAL_CONFIG
    PERSONAL_CONFIG = config.model_dump()


def get_config(key: str, default=None):
    keys = key.split(".")
    current = PERSONAL_CONFIG
    for k in keys:
        if isinstance(current, dict) and k in current:
            current = current[k]
        else:
            return default
    return current
