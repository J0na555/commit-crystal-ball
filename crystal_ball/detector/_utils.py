from dataclasses import dataclass


@dataclass
class Finding:
    check_id: str
    message: str
    line: int
    snippet: str
    suggested_fix: str
    severity: str  # "high" | "medium" | "low"


def get_line_snippet(lines: list[str], line_no: int) -> str:
    """Get a snippet for the given line number (1-based)."""
    if 0 <= line_no - 1 < len(lines):
        return lines[line_no - 1].strip()
    return ""
