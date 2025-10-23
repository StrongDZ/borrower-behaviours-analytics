import click
from src.cli.protocols_cli import analyze_protocols
from src.cli.abi_events_cli import extract_abi_events


@click.group()
def cli():
    """DeFi Llama Analysis CLI."""
    pass


# Register commands
cli.add_command(analyze_protocols)
cli.add_command(extract_abi_events)


if __name__ == "__main__":
    cli()
