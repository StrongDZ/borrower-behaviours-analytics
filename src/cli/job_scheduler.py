import click
from src.jobs.job_scheduler import JobScheduler
from src.utils.logger_utils import get_logger

logger = get_logger("Job Scheduler CLI")


@click.command(context_settings=dict(help_option_names=["-h", "--help"]))
def job_scheduler():
    """
    Chạy job scheduler để quản lý tất cả các job:
    - ETL Raw Data: chạy liên tục cả ngày
    - Prune Outdate Transactions & Label Accounts: chạy hằng ngày lúc 0h
    """
    try:
        scheduler = JobScheduler()
        logger.info("Starting Job Scheduler...")
        scheduler.run()
    except KeyboardInterrupt:
        logger.info("Job Scheduler stopped by user")
    except Exception as e:
        logger.error(f"Job Scheduler failed: {e}")
        raise
