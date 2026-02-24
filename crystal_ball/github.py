"""GitHub Actions annotation output for Crystal Ball.

Emits ``::error`` / ``::warning`` / ``::notice`` workflow commands so that
findings appear as inline annotations on pull-request diffs.  Works entirely
offline — no API tokens required.
"""

from __future__ import annotations

import sys
from typing import TextIO

from crystal_ball.detector._utils import Finding

_SEVERITY_TO_LEVEL = {
    "critical": "error",
    "high": "error",
    "medium": "warning",
    "low": "notice",
}


def format_annotation(finding: Finding, filepath: str) -> str:
    """Return a single GitHub Actions annotation line for *finding*."""
    level = _SEVERITY_TO_LEVEL.get(finding.severity.lower(), "warning")
    title = f"[{finding.severity.upper()}] {finding.check_id}"
    msg = f"{finding.message}. Fix: {finding.suggested_fix}"
    return f"::{level} file={filepath},line={finding.line},title={title}::{msg}"


def print_github_annotations(
    findings: list[Finding],
    filepath: str,
    *,
    stream: TextIO | None = None,
) -> None:
    """Write GitHub-compatible annotation lines for every finding."""
    out = stream or sys.stdout
    for finding in findings:
        out.write(format_annotation(finding, filepath) + "\n")
