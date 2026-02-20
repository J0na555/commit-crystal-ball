import typer
from pathlib import Path

from crystal_ball.detector import scan as scan_detector
from crystal_ball.narrator import ALL_TONES, DEFAULT_TONE
from crystal_ball.reporter import print_findings

app = typer.Typer(no_args_is_help=True)

_tone_help = f"Narrative tone: {', '.join(ALL_TONES)}"


@app.command()
def scan(
    files: list[Path] = typer.Argument(..., help="One or more file paths to scan"),
    tone: str = typer.Option(DEFAULT_TONE, "--tone", "-t", help=_tone_help),
) -> None:
    if tone not in ALL_TONES:
        typer.echo(
            f"Error: unknown tone '{tone}'. Choose from: {', '.join(ALL_TONES)}",
            err=True,
        )
        raise typer.Exit(1)

    for filepath in files:
        if not filepath.exists():
            typer.echo(f"Error: {filepath} does not exist", err=True)
            raise typer.Exit(1)
        if not filepath.is_file():
            typer.echo(f"Error: {filepath} is not a file", err=True)
            raise typer.Exit(1)

        content = filepath.read_text()
        findings = scan_detector(content, str(filepath))
        print_findings(findings, str(filepath), tone=tone)  # type: ignore[arg-type]


@app.command()
def version():
    typer.echo("0.1.0")


if __name__ == "__main__":
    typer.run(app)
