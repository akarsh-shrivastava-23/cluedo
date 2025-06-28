"""Tests for the exec_map module."""

from pathlib import Path

import pytest

from runner.exec_map import command_for_file, UnsupportedScriptError


def test_supported_extensions(tmp_path: Path) -> None:
    """Each supported extension maps to the correct command."""
    files_and_cmds = {
        "foo.py": ["python3"],
        "bar.sh": ["/bin/sh"],
        "baz.go": ["go", "run"],
        "qux.mongo": ["mongosh"],
        "norf.js": ["mongosh"],
    }
    for name, cmd in files_and_cmds.items():
        path = tmp_path / name
        path.touch()
        assert command_for_file(path) == cmd + [str(path)]


def test_unsupported_extension(tmp_path: Path) -> None:
    """Unsupported extensions raise an error."""
    path = tmp_path / "foo.txt"
    path.touch()
    with pytest.raises(UnsupportedScriptError):
        command_for_file(path)
