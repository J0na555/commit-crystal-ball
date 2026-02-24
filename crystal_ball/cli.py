from __future__ import annotations

import sys
from pathlib import Path

import typer

from crystal_ball import __version__
from crystal_ball.detector import has_blocking, scan as scan_detector, scan_diff
from crystal_ball.formatter import format_findings
from crystal_ball.git import (
    ChangedFile,
    find_git_root,
    get_staged_content,
    get_staged_files,
    install_hook,
    parse_staged_diff,
    file_too_large,
    MAX_FILE_SIZE,
)
from crystal_ball.github import print_github_annotations
from crystal_ball.narrator import ALL_TONES, DEFAULT_TONE

app = typer.Typer(no_args_is_help=True)

_tone_help = f"Narrative tone: {', '.join(ALL_TONES)}"


@app.command()
def scan(
    files: list[Path] = typer.Argument(..., help="One or more file paths to scan"),
    tone: str = typer.Option(DEFAULT_TONE, "--tone", "-t", help=_tone_help),
    github: bool = typer.Option(False, "--github", help="Emit GitHub Actions annotations"),
    diff_aware: bool = typer.Option(False, "--diff-aware", help="Only report on changed lines (requires git)"),
) -> None:
    """Scan one or more files for security and reliability issues."""
    if tone not in ALL_TONES:
        typer.echo(
            f"Error: unknown tone '{tone}'. Choose from: {', '.join(ALL_TONES)}",
            err=True,
        )
        raise typer.Exit(1)

    changed_map: dict[str, set[int]] = {}
    if diff_aware:
        for cf in parse_staged_diff():
            changed_map[cf.filepath] = cf.added_lines

    all_findings = []

    for filepath in files:
        if not filepath.exists():
            typer.echo(f"Error: {filepath} does not exist", err=True)
            raise typer.Exit(1)
        if not filepath.is_file():
            typer.echo(f"Error: {filepath} is not a file", err=True)
            raise typer.Exit(1)
        if file_too_large(str(filepath)):
            typer.echo(f"Skipping {filepath} (exceeds {MAX_FILE_SIZE // 1024}KiB limit)", err=True)
            continue

        content = filepath.read_text()
        fpath = str(filepath)

        if diff_aware and fpath in changed_map:
            findings = scan_diff(content, fpath, changed_map[fpath])
        else:
            findings = scan_detector(content, fpath)

        all_findings.extend(findings)

        if github:
            print_github_annotations(findings, fpath)
        else:
            format_findings(findings, fpath, tone=tone)  # type: ignore[arg-type]

    if has_blocking(all_findings):
        raise typer.Exit(1)


@app.command("scan-staged")
def scan_staged(
    tone: str = typer.Option(DEFAULT_TONE, "--tone", "-t", help=_tone_help),
    github: bool = typer.Option(False, "--github", help="Emit GitHub Actions annotations"),
    full_file: bool = typer.Option(False, "--full-file", help="Scan entire files instead of changed lines only"),
) -> None:
    """Scan staged Git files (pre-commit mode).

    By default only lines that appear in the diff are reported.
    Use --full-file to scan entire staged files.
    """
    if tone not in ALL_TONES:
        typer.echo(
            f"Error: unknown tone '{tone}'. Choose from: {', '.join(ALL_TONES)}",
            err=True,
        )
        raise typer.Exit(1)

    if find_git_root() is None:
        typer.echo("Error: not inside a Git repository", err=True)
        raise typer.Exit(1)

    staged = get_staged_files()
    if not staged:
        raise typer.Exit(0)

    changed_map: dict[str, set[int]] = {}
    if not full_file:
        for cf in parse_staged_diff():
            changed_map[cf.filepath] = cf.added_lines

    all_findings = []

    for fpath in staged:
        content = get_staged_content(fpath)
        if content is None:
            continue
        if len(content.encode()) > MAX_FILE_SIZE:
            typer.echo(f"Skipping {fpath} (exceeds {MAX_FILE_SIZE // 1024}KiB limit)", err=True)
            continue

        if full_file or fpath not in changed_map:
            findings = scan_detector(content, fpath)
        else:
            findings = scan_diff(content, fpath, changed_map[fpath])

        all_findings.extend(findings)

        if github:
            print_github_annotations(findings, fpath)
        else:
            format_findings(findings, fpath, tone=tone)  # type: ignore[arg-type]

    if has_blocking(all_findings):
        raise typer.Exit(1)


@app.command()
def install() -> None:
    """Install the Crystal Ball pre-commit hook into the current Git repository."""
    try:
        hook_path = install_hook()
    except RuntimeError as exc:
        typer.echo(f"Error: {exc}", err=True)
        raise typer.Exit(1)

    typer.echo(f"Pre-commit hook installed at {hook_path}")
    typer.echo("Crystal Ball will now scan staged files on every commit.")
    typer.echo("Bypass with: git commit --no-verify")


@app.command()
def version():
    typer.echo(__version__)


def main() -> None:
    """CLI entry point."""
    app()


if __name__ == "__main__":
    main()
