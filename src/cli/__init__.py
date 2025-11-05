import click
from src.cli.job_scheduler import job_scheduler


@click.group()
def cli():
    """Whale Selection CLI."""
    pass


# Register commands
cli.add_command(job_scheduler, "job_scheduler")


if __name__ == "__main__":
    cli()
