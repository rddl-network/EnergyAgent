import functools
import logging
import os
import sys

from loguru import logger

LOG_LEVEL = logging.getLevelName(os.getenv("LOG_LEVEL", "DEBUG"))
JSON_LOGS = False if os.getenv("JSON_LOGS") == "0" else True
LOG_FILE_PATH = os.getenv("LOG_FILE_PATH")
LOG_ROTATION_SIZE = os.getenv("LOG_ROTATION_SIZE", "100 MB")
LOG_RETENTION = os.getenv("LOG_RETENTION", "1 month")
DISABLE_THIRD_PARTY_LOG = False if os.getenv("DISABLE_THIRD_PARTY_LOG", "0") == "0" else True


# If we want to disable the logs of a third party app, we can add it to this list and vice versa
log_disabled_third_party_apps_list = ["pika", "urllib3", "asyncio", "web3"]


class InterceptHandler(logging.Handler):
    def emit(self, record):
        # Get corresponding Loguru level if it exists
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        # Find caller from where originated the logged message
        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging():
    # intercept everything at the root logger
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(LOG_LEVEL)

    # remove every other logger's handlers
    # and propagate to root logger
    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        if DISABLE_THIRD_PARTY_LOG and name in log_disabled_third_party_apps_list:
            # Disable the log propagation of the specific app to the root logger
            logging.getLogger(name).propagate = False
        else:
            logging.getLogger(name).propagate = True

    # configure loguru
    logger.remove()
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": JSON_LOGS, "level": LOG_LEVEL}])
    if LOG_FILE_PATH is not None:
        logger.add(
            LOG_FILE_PATH + "log-{time:YYYYMMDD-HHMM}.log",
            rotation=LOG_ROTATION_SIZE,
            retention=LOG_RETENTION,
            compression="zip",
            level=LOG_LEVEL,
        )


def log(func):
    @functools.wraps(func)
    def wrapper(*args, **kwargs):
        args_repr = [repr(a) for a in args]
        kwargs_repr = [f"{k}={v!r}" for k, v in kwargs.items()]
        signature = ", ".join(args_repr + kwargs_repr)
        logger.debug(f"function {func.__name__} called with args {signature}")
        try:
            result = func(*args, **kwargs)
            return result
        except Exception as e:
            logger.exception(f"Exception raised in {func.__name__}. exception: {str(e)}")
            raise e

    return wrapper
