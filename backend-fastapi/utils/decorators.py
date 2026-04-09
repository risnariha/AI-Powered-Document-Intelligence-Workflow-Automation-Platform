import time
import asyncio
from functools import wraps
from typing import Callable, Any
from tenacity import retry, stop_after_attempt, wait_exponential

from app.core.logger import logger


def timing_decorator(func: Callable) -> Callable:
    """Decorator to measure function execution time"""

    @wraps(func)
    async def async_wrapper(*args, **kwargs):
        start = time.time()
        result = await func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} took {duration:.2f}ms")
        return result

    @wraps(func)
    def sync_wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        duration = (time.time() - start) * 1000
        logger.debug(f"{func.__name__} took {duration:.2f}ms")
        return result

    if asyncio.iscoroutinefunction(func):
        return async_wrapper
    return sync_wrapper


def retry_decorator(max_attempts: int = 3, min_wait: int = 1, max_wait: int = 10):
    """Decorator to retry failed operations"""
    return retry(
        stop=stop_after_attempt(max_attempts),
        wait=wait_exponential(multiplier=1, min=min_wait, max=max_wait),
        reraise=True
    )