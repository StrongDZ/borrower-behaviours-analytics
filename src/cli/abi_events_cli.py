"""
ABI Events CLI
"""

import click
import sys
from ..jobs.abi_events_job import ABIEventsJob

@click.command(name="extract-abi-events", context_settings=dict(help_option_names=["-h", "--help"]))
@click.argument("abi_file", type=click.Path(exists=True))
@click.argument("target_file", type=click.Path())
def extract_abi_events(abi_file, target_file):
    """Extract ABI events from JSON file"""
    job = ABIEventsJob()

    try:
        click.echo(f"Extracting events from {abi_file} to {target_file}...")
        result = job.extract_events(abi_file, target_file, False)

        if result["success"]:
            summary = result["summary"]
            click.echo(f"✅ Successfully processed events!")
            click.echo(f"Total events: {summary['total_events']}")
            click.echo(f"Unique signatures: {summary['unique_signatures']}")
            click.echo("\nEvent names:")
            for i, name in enumerate(summary["event_names"], 1):
                click.echo(f"  {i}. {name}")
        else:
            click.echo(f"❌ Error extracting events: {result['error']}")
            sys.exit(1)

        click.echo("\n✅ Successfully completed!")

    except Exception as e:
        click.echo(f"❌ Error: {e}")
        sys.exit(1)
