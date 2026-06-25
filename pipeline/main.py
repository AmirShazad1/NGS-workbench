import sys
from pathlib import Path

import click

from pipeline.utils.config import load_config
from pipeline.utils.logger import setup_logger
from pipeline.utils.samplesheet import load_sample_sheet
from pipeline.workflows.full_pipeline import run_batch_pipeline, run_full_pipeline

logger = setup_logger(__name__)


@click.group()
def cli():
    """NGS Data Processing Pipeline CLI"""


@cli.command()
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to YAML config file",
)
@click.option("--output", "output_dir", required=True, type=click.Path(), help="Output directory")
def run(config_path, output_dir):
    """Run the full NGS pipeline for a single sample."""
    click.echo("Starting NGS pipeline...")
    try:
        config = load_config(config_path)
        config["output_dir"] = output_dir
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        summary = run_full_pipeline(config)
        click.echo(f"Pipeline completed: {summary}")
    except Exception as e:
        click.echo(f"Pipeline failed: {e}", err=True)
        sys.exit(1)


@cli.command(name="run-batch")
@click.option(
    "--config",
    "config_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to base YAML config (shared defaults)",
)
@click.option(
    "--sample-sheet",
    "sample_sheet_path",
    required=True,
    type=click.Path(exists=True),
    help="Path to CSV sample sheet",
)
@click.option("--output", "output_dir", required=True, type=click.Path(), help="Output directory")
def run_batch(config_path, sample_sheet_path, output_dir):
    """Run the full NGS pipeline across multiple samples from a sample sheet."""
    click.echo("Starting NGS batch pipeline...")
    try:
        base_config = load_config(config_path, strict=False)
        Path(output_dir).mkdir(parents=True, exist_ok=True)
        sample_configs = load_sample_sheet(sample_sheet_path, base_config, output_dir)
        summaries = run_batch_pipeline(sample_configs, output_dir)
        failed = [s for s in summaries if s["status"] != "completed"]
        click.echo(f"Batch completed: {len(summaries)} samples, {len(failed)} failed")
        for s in summaries:
            click.echo(f"  {s['sample_id']}: {s['status']}")
        if failed:
            sys.exit(1)
    except Exception as e:
        click.echo(f"Batch pipeline failed: {e}", err=True)
        sys.exit(1)


if __name__ == "__main__":
    cli()
