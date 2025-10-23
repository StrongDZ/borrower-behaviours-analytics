"""
Protocols CLI
"""

import click
import sys
from ..jobs.protocol_analysis_job import ProtocolAnalysisJob
from ..constants.api import DEFAULT_TOP_COUNT


@click.command(name="get-top-protocols", context_settings=dict(help_option_names=["-h", "--help"]))
@click.option("--categories", "-c", multiple=True, help="Categories to analyze (e.g., Lending, Dexs, Derivatives)")
@click.option(
    "--top-count", "-n", default=DEFAULT_TOP_COUNT, type=int, help=f"Number of top protocols to return per category (default: {DEFAULT_TOP_COUNT})"
)
@click.option("--all", "analyze_all", is_flag=True, help="Analyze all protocols instead of specific categories")
def analyze_protocols(categories, top_count, analyze_all):
    """Analyze DeFi protocols"""
    job = ProtocolAnalysisJob()

    try:
        if analyze_all:
            click.echo("🔍 Analyzing all protocols...")
            result = job.analyze_all_protocols(top_count)
        else:
            if not categories:
                click.echo("❌ Please specify categories with --categories or use --all for all protocols")
                return

            click.echo(f"🔍 Analyzing categories: {', '.join(categories)}")
            result = job.analyze_custom_categories(list(categories), top_count)

        if result:
            click.echo("✅ Analysis completed successfully!")
        else:
            click.echo("❌ No data found for analysis")

    except Exception as e:
        click.echo(f"❌ Error during analysis: {e}")
        sys.exit(1)
