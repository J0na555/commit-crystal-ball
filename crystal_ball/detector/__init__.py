import ast

from crystal_ball.detector._utils import Finding, has_blocking
from crystal_ball.detector.reliability import check_bare_except, check_requests_timeout
from crystal_ball.detector.secrets import check_hardcoded_secrets
from crystal_ball.detector.security import (
    check_eval_usage,
    check_sql_injection,
    check_subprocess_shell,
    check_yaml_load,
)

__all__ = ["Finding", "has_blocking", "scan", "scan_diff"]


def scan(content: str, filepath: str) -> list[Finding]:
    """Scan file content for potential issues. Returns list of findings."""
    findings: list[Finding] = []

    try:
        tree = ast.parse(content)
    except SyntaxError:
        return findings

    lines = content.splitlines()

    for node in ast.walk(tree):
        if isinstance(node, ast.Call):
            check_requests_timeout(node, lines, findings)
            check_eval_usage(node, lines, findings)
            check_sql_injection(node, lines, findings)
            check_subprocess_shell(node, lines, findings)
            check_yaml_load(node, lines, findings)
        if isinstance(node, ast.ExceptHandler):
            check_bare_except(node, lines, findings)

    check_hardcoded_secrets(lines, findings)

    return findings


def scan_diff(
    content: str,
    filepath: str,
    changed_lines: set[int],
) -> list[Finding]:
    """Scan *content* but only report findings on *changed_lines*.

    This keeps AST parsing whole-file (required for correctness) while
    filtering results to the diff, achieving O(n) over changed lines for
    the reporting step.
    """
    all_findings = scan(content, filepath)
    if not changed_lines:
        return all_findings
    return [f for f in all_findings if f.line in changed_lines]
