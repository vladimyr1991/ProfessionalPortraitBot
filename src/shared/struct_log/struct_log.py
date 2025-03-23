import logging
import os
import typing as t

import structlog
from .data_schemas import LogLevel

__all__ = [
    "logger"
    ]

LOG_LEVEL = os.environ.get("LOG_LEVEL")

try:
    log_level = LogLevel(LOG_LEVEL)
except Exception as e:
    raise ValueError("LOG_LEVEL must be one of DEBUG, INFO, WARNING, ERROR")


def set_logger() -> structlog.stdlib.BoundLogger:
    def set_process_id(
            _: t.Any, __: str, event_dict: t.MutableMapping[str, t.Any]
            ) -> t.Union[t.Mapping[str, t.Any], str, bytes, bytearray, tuple]:
        event_dict["process_id"] = os.getpid()
        return event_dict

    structlog.configure(
        wrapper_class=structlog.make_filtering_bound_logger(
            getattr(logging, log_level.value)
            ),
        processors=[
            structlog.processors.TimeStamper(fmt="iso"),
            structlog.processors.add_log_level,
            set_process_id,
            structlog.processors.JSONRenderer(),
            ],
        )
    return structlog.get_logger()


logger = set_logger()
