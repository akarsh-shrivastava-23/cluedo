"""Tests for the k8s script runner CLI."""

from pathlib import Path
from click.testing import CliRunner

# Ensure the parent directory is on the Python path so ``runner`` can be imported
import os
import sys

sys.path.insert(0, os.path.dirname(os.path.dirname(__file__)))

from runner.cli import main


def test_help() -> None:
    """Ensure the help command exits with code 0."""
    runner = CliRunner()
    result = runner.invoke(main, ["--help"])
    assert result.exit_code == 0


def test_run_script_file(tmp_path: Path) -> None:
    """Running with only --script-file executes the given file."""
    script = tmp_path / "hello.py"
    script.write_text("print('hello')")
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--script-file", str(script)])
    assert result.exit_code == 0


def test_run_query_file(tmp_path: Path) -> None:
    """Running with only --query-file executes the file."""
    script = tmp_path / "hello.sh"
    script.write_text("echo hi")
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--query-file", str(script)])
    assert result.exit_code == 0


def test_run_both_files(tmp_path: Path) -> None:
    """When both options are given, script-file is preferred."""
    script = tmp_path / "script.py"
    script.write_text("print('script')")
    query = tmp_path / "query.sh"
    query.write_text("echo query")
    runner = CliRunner()
    result = runner.invoke(
        main,
        ["run", "--script-file", str(script), "--query-file", str(query)],
    )
    assert result.exit_code == 0


def test_run_missing_options() -> None:
    """Fail when no options are provided."""
    runner = CliRunner()
    result = runner.invoke(main, ["run"])
    assert result.exit_code != 0


def test_exit_status_propagated(tmp_path: Path) -> None:
    """Non-zero exit codes from scripts are returned by the CLI."""
    script = tmp_path / "bad.sh"
    script.write_text("exit 3")
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--script-file", str(script)])
    assert result.exit_code == 3


def test_run_unsupported_extension(tmp_path: Path) -> None:
    """Unsupported extensions fail with a message."""
    script = tmp_path / "foo.txt"
    script.write_text("nothing")
    runner = CliRunner()
    result = runner.invoke(main, ["run", "--script-file", str(script)])
    assert result.exit_code != 0
    assert "Unsupported script type" in result.output


def test_verbose_outputs_debug(tmp_path: Path) -> None:
    """Verbose flag triggers debug output."""
    script = tmp_path / "hello.py"
    script.write_text("print('hi')")
    runner = CliRunner()
    result = runner.invoke(main, ["--verbose", "run", "--script-file", str(script)])
    assert result.exit_code == 0
    assert "Executing" in result.output
