import time
from datetime import datetime

from src.utils.logger_utils import get_logger
from src.constants.time_constants import TimeConstants

logger = get_logger("Time utils")


def round_timestamp(timestamp, round_time=86400):
    timestamp = int(timestamp)
    timestamp_unit_day = timestamp / round_time
    recover_to_unit_second = int(timestamp_unit_day) * round_time
    return recover_to_unit_second
