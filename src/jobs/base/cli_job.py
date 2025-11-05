
import time
from constants.time_constants import SLEEP_DURATION
from utils.logger_utils import get_logger
from utils.time_utils import round_timestamp
logger = get_logger('CLI Job')

class CLIJob:
    def __init__(self, interval=None, end_timestamp=None, retry=True):
        self.interval = interval
        self.end_timestamp = end_timestamp
        self.retry = retry

    def run(self, *args, **kwargs):
        self._pre_start()
        while True:
            try:
                self._start()
                self._execute(*args, **kwargs)
            except Exception as ex:
                logger.exception(ex)
                logger.warning('Something went wrong!!!')
                if self.retry:
                    self._retry()
                    continue
            self._end()
            if not self.interval:
                break
            next_synced_timestamp = self._get_next_synced_timestamp()
            if self._check_finish(next_synced_timestamp):
                break
            time_sleep = next_synced_timestamp - time.time()
            if time_sleep > 0:
                logger.info(f'Sleep {round(time_sleep, 3)} seconds')
                time.sleep(time_sleep)
        self._follow_end()

    def _get_next_synced_timestamp(self):
        return round_timestamp(int(time.time()), round_time=self.interval) + self.interval

    def _pre_start(self): pass
    def _start(self): pass
    def _end(self): pass
    def _follow_end(self): pass
    def _check_finish(self, next_synced_timestamp):
        if self.interval is None: return True
        if (self.end_timestamp is not None) and (next_synced_timestamp > self.end_timestamp): return True
        return False
    def _execute(self, *args, **kwargs): pass
    def _retry(self):
        logger.warning(f'Try again after {SLEEP_DURATION} seconds ...')
        time.sleep(SLEEP_DURATION)
