from __future__ import annotations

import os
import sys
from typing import TextIO

from crystal_ball.detector._utils import Finding
from crystal_ball.narrator import DEFAULT_TONE, ToneMode, format_narrative


class _Ansi:
    """Thin ANSI escape-code helper with automatic no-colour fallback."""

    RESET = "\033[0m"
    BOLD = "\033[1m"
    DIM = "\033[2m"

    BLUE = "\033[34m"
    YELLOW = "\033[33m"
    RED = "\033[31m"
    BOLD_RED = "\033[1;31m"
    CYAN = "\033[36m"
    MAGENTA = "\033[35m"

    def __init__(self, *, colour: bool | None = None) -> None:
        if colour is None:
            colour = _supports_colour()
        self._enabled = colour

    def style(self, text: str, code: str) -> str:
        if not self._enabled:
            return text
        return f"{code}{text}{self.RESET}"


def _supports_colour() -> bool:
    if os.environ.get("NO_COLOR"):
        return False
    if os.environ.get("FORCE_COLOR"):
        return True
    stream = sys.stdout
    return hasattr(stream, "isatty") and stream.isatty()


_SEVERITY_CODES = {
    "low": _Ansi.BLUE,
    "medium": _Ansi.YELLOW,
    "high": _Ansi.RED,
    "critical": _Ansi.BOLD_RED,
}

_SEVERITY_LABELS = {
    "low": "LOW",
    "medium": "MEDIUM",
    "high": "HIGH",
    "critical": "CRITICAL",
}


def format_findings(
    findings: list[Finding],
    filepath: str,
    *,
    tone: ToneMode = DEFAULT_TONE,
    colour: bool | None = None,
    stream: TextIO | None = None,
) -> None:
    """Write formatted findings to *stream* (defaults to ``sys.stdout``)."""
    if not findings:
        return

    out = stream or sys.stdout
    ansi = _Ansi(colour=colour)

    out.write(
        ansi.style(
            f"\n\U0001f52e Crystal Ball — {filepath}\n",
            _Ansi.BOLD + _Ansi.MAGENTA,
        )
    )
    out.write(ansi.style("─" * 60 + "\n", _Ansi.DIM))

    for finding in findings:
        narrative = format_narrative(finding, tone=tone)
        sev = finding.severity.lower()
        sev_code = _SEVERITY_CODES.get(sev, "")
        sev_label = _SEVERITY_LABELS.get(sev, finding.severity.upper())

        out.write("\n")
        out.write(ansi.style(f"  [{sev_label}] ", sev_code))
        out.write(ansi.style(narrative.headline, _Ansi.BOLD) + "\n")
        out.write(ansi.style(f"  Check   : ", _Ansi.CYAN) + f"{finding.check_id}\n")
        out.write(ansi.style(f"  Line    : ", _Ansi.CYAN) + f"{finding.line}\n")
        out.write(ansi.style(f"  Snippet : ", _Ansi.CYAN) + f"{finding.snippet}\n")
        out.write(ansi.style(f"  Risk    : ", _Ansi.CYAN) + f"{narrative.risk_summary}\n")
        out.write(
            ansi.style(f"  Fix     : ", _Ansi.CYAN)
            + ansi.style(finding.suggested_fix, _Ansi.BOLD)
            + "\n"
        )

    out.write("\n" + ansi.style("─" * 60 + "\n", _Ansi.DIM))

    highs = sum(1 for f in findings if f.severity.lower() in ("high", "critical"))
    total = len(findings)
    summary = f"  {total} finding(s), {highs} blocking (HIGH/CRITICAL)\n"
    if highs:
        out.write(ansi.style(summary, _Ansi.BOLD_RED))
    else:
        out.write(ansi.style(summary, _Ansi.YELLOW))
    out.write("\n")
