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
            "high": "bold red",
            "medium": "bold yellow",
            "low": "dim",
        }.get(finding.severity, "")

        table = Table(show_header=False, box=None, padding=(0, 1))
        table.add_column(style="bold cyan")
        table.add_column()

        table.add_row("Incident Type:", f"[{severity_style}]{finding.check_id}[/]")
        table.add_row("Prediction:", finding.message)
        table.add_row("Estimated Damage:", narrative.risk_summary)
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
