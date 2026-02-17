import ast

from crystal_ball.detector._utils import Finding
from crystal_ball.detector.reliability import check_bare_except, check_requests_timeout
from crystal_ball.detector.secrets import check_hardcoded_secrets
from crystal_ball.detector.security import (
    check_eval_usage,
    check_sql_injection,
    check_subprocess_shell,
    check_yaml_load,
)

__all__ = ["Finding", "scan"]


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
