from functools import wraps
import time

from src.utils.logger_utils import get_logger

logger = get_logger("RetryHandler")


class RetryStrategy:
    EXPONENTIAL = 'exponential'
    MULTIPLICATIVE = 'multiplicative'
    LINEAR = 'linear'
    CONSTANT = 'constant'

def retry(retries_number: int = 3, sleep_time: float = 1, strategy: str = RetryStrategy.EXPONENTIAL):
    def decorator(func):
        @wraps(func)
        def wrapper(*args, **kwargs):
            for attempt in range(1, retries_number + 1):
                try:
                    return func(*args, **kwargs)
                except Exception as ex:
                    logger.error(f'Error at {func.__name__}: {ex}')
                    if attempt == retries_number:
                        raise
                    logger.info(f"Retrying {attempt}/{retries_number} times")
                    
                    time_sleep_retry = calculate_retry_time(strategy, sleep_time, attempt)
                    logger.info(f"Retrying in {time_sleep_retry} seconds")
                    time.sleep(time_sleep_retry)
        return wrapper
    return decorator



def calculate_retry_time(strategy: str, time_sleep: float, _retry_time: int):
    if strategy == RetryStrategy.EXPONENTIAL:
        return time_sleep * 2 ** _retry_time
    elif strategy == RetryStrategy.MULTIPLICATIVE:
        return time_sleep * _retry_time
    elif strategy == RetryStrategy.LINEAR:
        return time_sleep + _retry_time
    elif strategy == RetryStrategy.CONSTANT:
        return time_sleep


