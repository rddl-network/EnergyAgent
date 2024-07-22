import functools
import logging
import sys

from typing import List, Optional
from loguru import logger
from pydantic import BaseModel

log_disabled_third_party_apps_list = []


class LogEntry(BaseModel):
    timestamp: str
    level: str
    message: str


class LogFilter(BaseModel):
    level: Optional[str] = None
    start_date: Optional[str] = None
    end_date: Optional[str] = None


class InterceptHandler(logging.Handler):
    def emit(self, record):
        try:
            level = logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        logger.opt(depth=depth, exception=record.exc_info).log(level, record.getMessage())


def setup_logging(
    log_level: str,
    json_logs: str,
    log_rotation_size: str,
    log_retention: str,
    disable_third_party_log: str,
    log_file_path: str,
):
    logging.root.handlers = [InterceptHandler()]
    logging.root.setLevel(log_level)

    for name in logging.root.manager.loggerDict.keys():
        logging.getLogger(name).handlers = []
        if disable_third_party_log and name in log_disabled_third_party_apps_list:
            logging.getLogger(name).propagate = False
        else:
            logging.getLogger(name).propagate = True

    logger.remove()
    logger.configure(handlers=[{"sink": sys.stdout, "serialize": json_logs, "level": log_level}])
    logger.add(
        log_file_path + "log-{time:YYYYMMDD-HHMM}.log",
        rotation=log_rotation_size,
        retention=log_retention,
        compression="zip",
        level=log_level,
    )


def get_logs(log_file_path: str, limit: int = 100, filter: LogFilter = None) -> List[LogEntry]:
    try:
        with open(log_file_path, "r") as log_file:
            logs = log_file.readlines()[-limit:]

        parsed_logs = []
        for log in logs:
            parts = log.split("|")
            if len(parts) >= 3:
                timestamp, level, message = parts[0], parts[1], "|".join(parts[2:])
                log_entry = LogEntry(
                    timestamp=timestamp.strip(),
                    level=level.strip(),
                    message=message.strip(),
                )

                if filter:
                    if filter.level and log_entry.level != filter.level:
                        continue
                    if filter.start_date and log_entry.timestamp < filter.start_date:
                        continue
                    if filter.end_date and log_entry.timestamp > filter.end_date:
                        continue

                parsed_logs.append(log_entry)

        return parsed_logs
    except Exception as e:
        logger.error(f"Failed to retrieve logs: {str(e)}")
        return []


def clear_logs(log_file_path: str):
    try:
        open(log_file_path, "w").close()
        logger.info("Logs cleared successfully")
        return True
    except Exception as e:
        logger.error(f"Failed to clear logs: {str(e)}")
        return False


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
