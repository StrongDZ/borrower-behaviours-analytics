from cli.job_scheduler import job_scheduler
from aggregator.borrower_aggregator import BorrowerAggregatorJob
import click

@click.group()
def cli():
    pass

cli.add_command(job_scheduler, "job_scheduler")

if __name__ == "__main__":
    cli()