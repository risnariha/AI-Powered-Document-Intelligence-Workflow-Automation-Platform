import logging
import sys
from datetime import datetime
from loguru import logger as loguru_logger
import json

from app.config import settings


class InterceptHandler(logging.Handler):
    """Intercept standard logging and redirect to loguru"""

    def emit(self, record: logging.LogRecord) -> None:
        try:
            level = loguru_logger.level(record.levelname).name
        except ValueError:
            level = record.levelno

        frame, depth = logging.currentframe(), 2
        while frame.f_code.co_filename == logging.__file__:
            frame = frame.f_back
            depth += 1

        loguru_logger.opt(depth=depth, exception=record.exc_info).log(
            level, record.getMessage()
        )


def setup_logging():
    """Configure logging for the application"""

    loguru_logger.remove()

    if settings.LOG_FORMAT == "json":
        def json_formatter(record):
            log_entry = {
                "timestamp": datetime.utcnow().isoformat(),
                "level": record["level"].name,
                "message": record["message"],
                "module": record["name"],
                "function": record["function"],
                "line": record["line"],
                "environment": settings.ENVIRONMENT
            }

            if record["exception"]:
                log_entry["exception"] = {
                    "type": record["exception"].type.__name__,
                    "value": str(record["exception"].value)
                }

            return json.dumps(log_entry) + "\n"

        loguru_logger.add(
            sys.stdout,
            format=json_formatter,
            level=settings.LOG_LEVEL,
            colorize=False
        )
    else:
        loguru_logger.add(
            sys.stdout,
            format="<green>{time:YYYY-MM-DD HH:mm:ss.SSS}</green> | <level>{level: <8}</level> | <cyan>{name}</cyan>:<cyan>{function}</cyan>:<cyan>{line}</cyan> - <level>{message}</level>",
            level=settings.LOG_LEVEL,
            colorize=True
        )

    # File logging for production
    if settings.is_production:
        loguru_logger.add(
            "logs/app_{time:YYYY-MM-DD}.log",
            rotation="1 day",
            retention="30 days",
            compression="zip",
            level="WARNING"
        )

    # Intercept standard logging
    logging.basicConfig(handlers=[InterceptHandler()], level=0, force=True)

    # Set specific loggers
    logging.getLogger("uvicorn.access").handlers = [InterceptHandler()]
    logging.getLogger("uvicorn.error").handlers = [InterceptHandler()]

    loguru_logger.info(f"Logging configured - Level: {settings.LOG_LEVEL}, Format: {settings.LOG_FORMAT}")
    return loguru_logger


logger = loguru_logger