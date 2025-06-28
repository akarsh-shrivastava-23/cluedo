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


def test_run_script_file():
    """Running with only --script-file succeeds."""
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--script-file", "foo"])
    assert result.exit_code == 0


def test_run_query_file():
    """Running with only --query-file succeeds."""
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--query-file", "bar"])
    assert result.exit_code == 0


def test_run_both_files():
    """Running with both options succeeds."""
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["run", "--script-file", "foo", "--query-file", "bar"],
    )
    assert result.exit_code == 0


def test_run_missing_options():
    """Fail when no options are provided."""
    runner = CliRunner()
    result = runner.invoke(main, ["run"])
    assert result.exit_code != 0


def test_verbose_outputs_debug():
    """Verbose flag triggers debug output."""
    runner = CliRunner()
    result = runner.invoke(main, ["--verbose", "run", "--script-file", "foo"])
    assert result.exit_code == 0
    assert "Running command" in result.output
