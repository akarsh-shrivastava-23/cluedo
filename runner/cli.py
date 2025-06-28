"""Command line interface for k8s script runner."""

from __future__ import annotations

import sys
import logging
from typing import Optional
from pathlib import Path
import subprocess

from .exec_map import command_for_file, UnsupportedScriptError

import click

try:
    from loguru import logger  # type: ignore

    LOGURU_AVAILABLE = True
except Exception:  # pragma: no cover - fallback if loguru is missing
    LOGURU_AVAILABLE = False
    logger = logging.getLogger("runner")


@click.group()
@click.option("--verbose", is_flag=True, help="Enable debug output.")
@click.pass_context
def main(ctx: click.Context, verbose: bool) -> None:
    """Entry point for the k8s script runner CLI."""
    if LOGURU_AVAILABLE:
        if verbose:
            logger.remove()  # type: ignore[operator]
            logger.add(sys.stderr, level="DEBUG")  # type: ignore[call-arg]
    else:
        logger.setLevel(logging.DEBUG if verbose else logging.INFO)
        logger.handlers.clear()
        handler = logging.StreamHandler(sys.stderr)
        formatter = logging.Formatter("%(levelname)s:%(message)s")
        handler.setFormatter(formatter)
        logger.addHandler(handler)


@main.command()
@click.option("--script-file", type=click.Path(), required=False)
@click.option("--query-file", type=click.Path(), required=False)
def run(script_file: Optional[str], query_file: Optional[str]) -> None:
    """Run a script or query."""
    if not script_file and not query_file:
        raise click.UsageError(
            "At least one of --script-file or --query-file is required."
        )
    file_to_run = Path(script_file or query_file)  # prefer script if both given
    try:
        cmd = command_for_file(file_to_run)
    except UnsupportedScriptError as exc:
        raise click.ClickException(str(exc)) from exc

    logger.debug("Executing %s", " ".join(cmd))
    result = subprocess.run(cmd)
    if result.returncode != 0:
        raise SystemExit(result.returncode)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
