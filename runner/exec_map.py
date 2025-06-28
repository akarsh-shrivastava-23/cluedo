"""Utility for mapping script filenames to execution commands."""

from __future__ import annotations

from pathlib import Path
from typing import List


class UnsupportedScriptError(Exception):
    """Raised when a script has an unrecognized file extension."""


_COMMAND_MAP = {
    ".py": ["python3"],
    ".sh": ["/bin/sh"],
    ".go": ["go", "run"],
    ".mongo": ["mongosh"],
    ".js": ["mongosh"],
}


def command_for_file(path: Path) -> List[str]:
    """Return the command required to execute ``path``.

    Parameters
    ----------
    path:
        The script file whose interpreter should be determined.

    Returns
    -------
    List[str]
        The command (as a list suitable for :func:`subprocess.run`) to execute
        the provided file.

    Raises
    ------
    UnsupportedScriptError
        If ``path`` has an extension that is not supported.
    """
    ext = path.suffix.lower()
    if ext not in _COMMAND_MAP:
        raise UnsupportedScriptError(f"Unsupported script type: {path}")
    return _COMMAND_MAP[ext] + [str(path)]


__all__ = ["UnsupportedScriptError", "command_for_file"]
