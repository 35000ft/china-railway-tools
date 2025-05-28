import logging
import os
from logging.handlers import RotatingFileHandler


def setup_logging():
    root_logger = logging.getLogger()
    root_logger.setLevel(logging.DEBUG)

    # 控制台输出
    console_handler = logging.StreamHandler()
    console_handler.setLevel(logging.INFO)
    console_fmt = logging.Formatter(
        '[%(asctime)s] %(levelname)s %(name)s: %(message)s',
        datefmt='%Y-%m-%d %H:%M:%S',
    )
    console_handler.setFormatter(console_fmt)
    root_logger.addHandler(console_handler)

    # 文件输出（可选：日志轮转）
    file_handler = RotatingFileHandler(
        filename=f'{os.path.join(os.getenv("WORK_DIR"), "logs/app.log")}',
        maxBytes=10 * 1024 * 1024,
        backupCount=5,
        encoding='utf-8'
    )
    file_handler.setLevel(logging.DEBUG)
    file_fmt = logging.Formatter(
        '%(asctime)s %(levelname)-5s %(name)-20s %(message)s'
    )
    file_handler.setFormatter(file_fmt)
    root_logger.addHandler(file_handler)
