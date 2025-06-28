"""Tests for the k8s script runner CLI."""

from click.testing import CliRunner

# Ensure the parent directory is on the Python path so ``runner`` can be imported
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from runner.cli import main


def test_help():
    """Ensure the help command exits with code 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0
