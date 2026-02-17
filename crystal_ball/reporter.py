from rich.console import Console
from rich.panel import Panel
from rich.table import Table

from crystal_ball.detector import Finding

console = Console()


def print_findings(findings: list[Finding], filepath: str) -> None:
    """Print findings for a file using rich formatting."""
    if not findings:
        return

    for finding in findings:
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
        table.add_row("Line:", str(finding.line))
        table.add_row("Snippet:", finding.snippet)
        table.add_row("Suggested Fix:", finding.suggested_fix)
        table.add_row("Estimated Damage:", "[dim]—[/]")

        panel = Panel(
            table,
            title=f"[bold]🔮 FLASHFORWARD DETECTED[/] — [dim]{filepath}:{finding.line}[/]",
            border_style="magenta",
        )
        console.print(panel)
        console.print()
