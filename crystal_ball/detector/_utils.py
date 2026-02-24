from dataclasses import dataclass

SEVERITY_ORDER = {"critical": 4, "high": 3, "medium": 2, "low": 1}
BLOCKING_SEVERITIES = frozenset({"high", "critical"})


@dataclass
class Finding:
    check_id: str
    message: str
    line: int
    snippet: str
    suggested_fix: str
    severity: str  # "critical" | "high" | "medium" | "low"

    @property
    def is_blocking(self) -> bool:
        return self.severity.lower() in BLOCKING_SEVERITIES


def get_line_snippet(lines: list[str], line_no: int) -> str:
    """Get a snippet for the given line number (1-based)."""
    if 0 <= line_no - 1 < len(lines):
        return lines[line_no - 1].strip()
    return ""


def has_blocking(findings: list[Finding]) -> bool:
    """Return True if any finding is HIGH or CRITICAL severity."""
    return any(f.is_blocking for f in findings)
