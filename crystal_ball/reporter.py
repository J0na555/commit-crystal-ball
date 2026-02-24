from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crystal_ball.detector import Finding
from crystal_ball.narrator import DEFAULT_TONE, ToneMode, format_narrative

console = Console()


def print_findings(
    findings: list[Finding],
    filepath: str,
    tone: ToneMode = DEFAULT_TONE,
) -> None:
    """Print findings for a file using rich formatting."""
    if not findings:
        return

    for finding in findings:
        narrative = format_narrative(finding, tone=tone)

        severity_style = {
            "critical": "bold red",
            "high": "red",
            "medium": "yellow",
            "low": "blue",
        }.get(finding.severity.lower(), "")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column()

        sev_label = finding.severity.upper()
        table.add_row("Severity:", f"[{severity_style}]{sev_label}[/]")
        table.add_row("Check:", f"[{severity_style}]{finding.check_id}[/]")
        table.add_row("Risk:", narrative.risk_summary)
        table.add_row("Line:", str(finding.line))
        table.add_row("Snippet:", finding.snippet)
        table.add_row("Suggested Fix:", finding.suggested_fix)

        panel = Panel(
            table,
            title=f"[bold]\U0001f52e {narrative.headline}[/] \u2014 [dim]{filepath}:{finding.line}[/]",
            border_style="magenta",
        )
        console.print(panel)
        console.print()
