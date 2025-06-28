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
@click.option("--pod", help="Run inside this Kubernetes pod", required=False)
@click.option("--namespace", default="default", show_default=True)
@click.option("--container", required=False, help="Container name")
@click.option("--artifact-dir", type=click.Path(file_okay=False), required=False)
@click.option("--context", required=False, help="Kubernetes context")
def run(
    script_file: Optional[str],
    query_file: Optional[str],
    pod: Optional[str],
    namespace: str,
    container: Optional[str],
    artifact_dir: Optional[str],
    context: Optional[str],
) -> None:
    """Run a script or query."""
    if not script_file and not query_file:
        raise click.UsageError(
            "At least one of --script-file or --query-file is required."
        )
    file_to_run = Path(script_file or query_file)  # prefer script if both given

    if pod:
        from .k8s import ensure_context, run_script_in_pod

        api = ensure_context(context)
        exit_code = run_script_in_pod(
            api,
            namespace,
            pod,
            file_to_run,
            container=container,
            artifact_dir=Path(artifact_dir or "."),
        )
        raise SystemExit(exit_code)

    try:
        cmd = command_for_file(file_to_run)
    except UnsupportedScriptError as exc:
        raise click.ClickException(str(exc)) from exc

    logger.debug("Executing %s", " ".join(cmd))
    result = subprocess.run(cmd)
    raise SystemExit(result.returncode)


if __name__ == "__main__":  # pragma: no cover - manual execution
    main()
