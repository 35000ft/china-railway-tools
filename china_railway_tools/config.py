# config.py
import os
from appdirs import user_data_dir

from china_railway_tools.schemas.AppConifg import AppConfig

APP_NAME = "CR_TOOLS"
APP_AUTHOR = "yunshang"

PERSONAL_CONFIG = {

}


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


def get_default_db_url():
    sqlite_dir = get_config("sqlite_dir")
    if not sqlite_dir:
        sqlite_dir = user_data_dir(APP_NAME, APP_AUTHOR)
    db_path = os.path.join(sqlite_dir, 'data.db')
    if not os.path.exists(os.path.dirname(db_path)):
        os.makedirs(os.path.dirname(db_path))
    return f"sqlite:///{db_path}"
