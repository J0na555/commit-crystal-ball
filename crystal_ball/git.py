from __future__ import annotations

import os
import re
import stat
import subprocess
from dataclasses import dataclass, field
from pathlib import Path

MAX_FILE_SIZE = 1_048_576  # 1 MiB — skip files larger than this
SUPPORTED_EXTENSIONS: tuple[str, ...] = (".py",)

# runs the precommit hook, which executes 'crystal scan-staged'
HOOK_SCRIPT = """\
#!/bin/sh
# Crystal Ball pre-commit hook
# Bypass with: git commit --no-verify
crystal scan-staged
"""


@dataclass
class ChangedFile:
    """A staged file together with the set of added/modified line numbers."""

    filepath: str
    added_lines: set[int] = field(default_factory=set)


def find_git_root() -> Path | None:
    """Return the repository root, or *None* if not inside a Git repo."""
    try:
        result = subprocess.run(
            ["git", "rev-parse", "--show-toplevel"],
            capture_output=True,
            text=True,
            check=True,
        )
        return Path(result.stdout.strip())
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


def install_hook() -> Path:
    """Write the pre-commit hook into ``.git/hooks/`` and make it executable.

    Raises
    ------
    RuntimeError
        If the working directory is not inside a Git repository.
    """
    git_root = find_git_root()
    if git_root is None:
        raise RuntimeError("Not inside a Git repository")

    hooks_dir = git_root / ".git" / "hooks"
    hooks_dir.mkdir(parents=True, exist_ok=True)

    hook_path = hooks_dir / "pre-commit"
    hook_path.write_text(HOOK_SCRIPT)
    hook_path.chmod(
        hook_path.stat().st_mode | stat.S_IXUSR | stat.S_IXGRP | stat.S_IXOTH
    )
    return hook_path


def get_staged_files(
    extensions: tuple[str, ...] = SUPPORTED_EXTENSIONS,
) -> list[str]:
    """Return staged file paths (added/copied/modified), filtered by extension."""
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "--name-only", "--diff-filter=ACM"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    paths = [p for p in result.stdout.strip().splitlines() if p]
    if extensions:
        paths = [p for p in paths if any(p.endswith(ext) for ext in extensions)]
    return paths


def get_staged_content(filepath: str) -> str | None:
    """Read a file's content from the Git index (staging area).

    Returns *None* when the file cannot be read (e.g. binary or missing).
    """
    try:
        result = subprocess.run(
            ["git", "show", f":{filepath}"],
            capture_output=True,
            text=True,
            check=True,
        )
        return result.stdout
    except (subprocess.CalledProcessError, FileNotFoundError):
        return None


_HUNK_RE = re.compile(r"^@@ -\d+(?:,\d+)? \+(\d+)(?:,(\d+))? @@")


def parse_staged_diff() -> list[ChangedFile]:
    """Parse ``git diff --cached -U0`` and return per-file changed line sets.

    Only *added* lines (``+`` prefix in the unified diff) are tracked.
    """
    try:
        result = subprocess.run(
            ["git", "diff", "--cached", "-U0"],
            capture_output=True,
            text=True,
            check=True,
        )
    except (subprocess.CalledProcessError, FileNotFoundError):
        return []

    files: dict[str, set[int]] = {}
    current_file: str | None = None

    for line in result.stdout.splitlines():
        if line.startswith("+++ b/"):
            current_file = line[6:]
        elif line.startswith("@@ ") and current_file is not None:
            m = _HUNK_RE.match(line)
            if m:
                start = int(m.group(1))
                count = int(m.group(2)) if m.group(2) is not None else 1
                if count > 0:
                    files.setdefault(current_file, set()).update(
                        range(start, start + count)
                    )

    return [ChangedFile(filepath=f, added_lines=lines) for f, lines in files.items()]


def file_too_large(filepath: str) -> bool:
    try:
        return os.path.getsize(filepath) > MAX_FILE_SIZE
    except OSError:
        return False
