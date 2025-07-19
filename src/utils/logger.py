import logging
import logging.config
from typing import Optional

LOGGING_CONFIG = {
    "version": 1,
    "disable_existing_loggers": False,
    "formatters": {
        "standard": {
            "format": "[%(asctime)s][%(levelname)s|%(filename)s:%(lineno)s] > %(message)s",
            "datefmt": "%Y-%m-%d %H:%M:%S",
        },
    },
    "handlers": {
        "console": {
            "class": "logging.StreamHandler",
            "formatter": "standard",
            "level": "INFO",
            "stream": "ext://sys.stdout",
        },
        # "file": {
        #     "class": "logging.FileHandler",
        #     "formatter": "standard",
        #     "level": "INFO",
        #     "filename": "analyst_robot.log",
        #     "encoding": "utf8",
        # },
    },
    "root": {
        "handlers": ["console"],
        "level": "INFO",
    },
}


def setup_logging() -> None:
    """
    should be called once in entrypoint (e.g. main.py) to setup logging for the entire project
    """
    logging.config.dictConfig(LOGGING_CONFIG)


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """
    should be called in each module to get logger for that module
    """
    return logging.getLogger(name)
